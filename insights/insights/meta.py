"""
file: insights/meta.py
importable: Meta, kind_of, METRICS, REEL_METRICS, DAY_METRICS, VERSION

Meta reads the Bitpulse Instagram account through the Graph API: its posts, the numbers of one
post, the numbers of the account for one day and who its audience is. The key and the account id come from the caller.

description: Reads Instagram posts and their numbers from the Meta Graph API.
"""

# NOTE: Meta does not give every number for every post. A post made before the account turned
# professional, or a kind of post a metric does not cover, makes the whole request fail. The
# metrics are then asked one by one and the ones Meta refuses are left out.
#
# XXX: The metric names follow the Graph API as it was when this was written, and Meta renames
# them from time to time. insights check prints what each one returns, and that is the first thing
# to run after a Meta change.

from typing import Any, Iterator, Optional
from urllib.parse import urlencode

from . import http

# --- Constants ---

BASE = "https://graph.facebook.com"
VERSION = "v27.0"
PAGE = 50
MEDIA_FIELDS = "id,caption,media_type,media_product_type,timestamp,permalink,thumbnail_url,media_url"
# Graph API name of a metric, then the name the Bitpulse API stores it under.
METRICS = {
    "views": "views",
    "reach": "reach",
    "likes": "likes",
    "comments": "comments",
    "saved": "saves",
    "shares": "shares",
    "total_interactions": "interactions",
    "reposts": "reposts",
}
REEL_METRICS = {
    "ig_reels_avg_watch_time": "watch_ms",
    "ig_reels_video_view_total_time": "watch_total_ms",
    "reels_skip_rate": "skip_rate",
}
# Numbers Meta gives with a decimal, kept as they are. Everything else is a count.
RATES = {"skip_rate"}
# website_clicks is the link in the bio. profile_links_taps sounds like it but counts the contact buttons.
DAY_METRICS = {
    "profile_views": "profile_views",
    "website_clicks": "link_taps",
    "profile_links_taps": "contact_taps",
    "reach": "reach",
    "views": "views",
    "accounts_engaged": "engaged",
    "total_interactions": "interactions",
    "likes": "likes",
    "comments": "comments",
    "shares": "shares",
    "saves": "saves",
}
# A metric split by follow_type, then the names its FOLLOWER and NON_FOLLOWER parts are stored under.
# For follows_and_unfollows Meta uses the same two words for a follow and an unfollow.
SPLITS = {
    "reach": ("reach_followers", "reach_others"),
    "views": ("views_followers", "views_others"),
    "follows_and_unfollows": ("follows", "unfollows"),
}
AUDIENCE = {"follower_demographics": "followers", "engaged_audience_demographics": "engaged"}
GROUPS = ("age", "gender", "country", "city")
KINDS = {"CAROUSEL_ALBUM": "carousel"}
REFUSED = 400

# --- Client ---

class Meta:
    """Reads one Instagram account.

    Args:
        token: System user key of the Bitpulse business portfolio.
        account: Instagram account id.
        version: Graph API version.
    """

    def __init__(self, token: str, account: str, version: str = VERSION):
        self.token = token
        self.account = account
        self.version = version

    # The key goes in a header, so it never ends up in an error message that prints the address.
    def _get(self, path: str, **query: Any) -> Any:
        url = f"{BASE}/{self.version}/{path}?{urlencode(query)}"
        return http.get_json(url, {"Authorization": f"Bearer {self.token}"})

    def profile(self) -> dict[str, Any]:
        return self._get(self.account, fields="username,followers_count,media_count")

    # Meta answers in pages and gives the address of the next one, which already holds the query.
    def posts(self) -> Iterator[dict[str, Any]]:
        """Yields every post of the account, newest first.

        Yields:
            Posts as Meta describes them, without stories.
        """
        answer = self._get(f"{self.account}/media", fields=MEDIA_FIELDS, limit=PAGE)
        while True:
            for item in answer.get("data", []):
                if item.get("media_product_type") != "STORY":
                    yield item
            following = answer.get("paging", {}).get("next")
            if not following:
                return
            answer = http.get_json(following, {"Authorization": f"Bearer {self.token}"})

    def counts(self, post: dict[str, Any]) -> dict[str, Optional[float]]:
        """Reads the lifetime numbers of one post.

        Args:
            post: A post as posts yields it.

        Returns:
            Numbers under the names the Bitpulse API uses. A number Meta refused is missing.
        """
        wanted = {**METRICS, **(REEL_METRICS if kind_of(post) == "reel" else {})}
        return self.metrics(post["id"], wanted)

    # The day runs from midnight to midnight UTC, the same day the counts table uses.
    def day(self, since: int, until: int) -> dict[str, Optional[float]]:
        """Reads the account numbers of one day.

        Args:
            since: Start of the day as a Unix time.
            until: End of the day as a Unix time.

        Returns:
            Numbers under the names the Bitpulse API uses. A number Meta refused is missing.
        """
        span = {"metric_type": "total_value", "period": "day", "since": since, "until": until}
        result = self.metrics(self.account, DAY_METRICS, **span)
        for name, (first, second) in SPLITS.items():
            try:
                parts = _parts(self._get(f"{self.account}/insights", metric=name, breakdown="follow_type", **span))
            except http.HttpError as error:
                if error.status != REFUSED:
                    raise
                continue
            if parts:
                result[first] = parts.get("FOLLOWER", 0)
                result[second] = parts.get("NON_FOLLOWER", 0)
        return result

    # Meta answers with an empty list below one hundred followers, which gives no rows here.
    def audience(self) -> list[dict[str, Any]]:
        """Reads who the followers and the engaged accounts are, and when the followers are online.

        Returns:
            Rows with the group, the breakdown, its value and the number of accounts.
        """
        rows: list[dict[str, Any]] = []
        for name, group in AUDIENCE.items():
            for breakdown in GROUPS:
                answer = self._get(f"{self.account}/insights", metric=name, metric_type="total_value", period="lifetime",
                                   timeframe="this_month", breakdown=breakdown)
                rows += [{"audience": group, "breakdown": breakdown, "key": key, "value": value} for key, value in _parts(answer).items()]
        online = self._get(f"{self.account}/insights", metric="online_followers", period="lifetime")
        for item in online.get("data", []):
            hours = (item.get("values") or [{}])[-1].get("value") or {}
            rows += [{"audience": "online", "breakdown": "hour", "key": str(hour), "value": int(count)}
                     for hour, count in hours.items() if isinstance(count, (int, float))]
        return rows

    # Asked all together first, which is one call for a normal post.
    def metrics(self, target: str, wanted: dict[str, str], **query: Any) -> dict[str, Optional[float]]:
        """Reads insights metrics of a post or of the account.

        Args:
            target: Post id or account id.
            wanted: Graph API metric names and the names to return them under.
            query: Extra query values such as period.

        Returns:
            The numbers Meta gave. A metric it refused is missing.

        Raises:
            http.HttpError: If Meta fails for another reason than refusing a metric.
        """
        try:
            return _values(self._get(f"{target}/insights", metric=",".join(wanted), **query), wanted)
        except http.HttpError as error:
            if error.status != REFUSED or len(wanted) == 1:
                raise
        result: dict[str, Optional[float]] = {}
        for name, ours in wanted.items():
            try:
                result |= _values(self._get(f"{target}/insights", metric=name, **query), {name: ours})
            except http.HttpError as error:
                if error.status != REFUSED:
                    raise
        return result

# --- Helpers ---

def kind_of(post: dict[str, Any]) -> str:
    if post.get("media_product_type") == "REELS":
        return "reel"
    return KINDS.get(post.get("media_type", ""), "image")


def _parts(answer: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in answer.get("data", []):
        for split in item.get("total_value", {}).get("breakdowns", []):
            for part in split.get("results", []):
                keys = part.get("dimension_values") or []
                if keys and isinstance(part.get("value"), (int, float)):
                    result[str(keys[0])[:120]] = int(part["value"])
    return result


# A post metric carries its number in values, an account metric asked as total_value in total_value.
def _values(answer: dict[str, Any], wanted: dict[str, str]) -> dict[str, Optional[float]]:
    result: dict[str, Optional[float]] = {}
    for item in answer.get("data", []):
        ours = wanted.get(item.get("name"))
        if ours is None:
            continue
        if "total_value" in item:
            value = item["total_value"].get("value")
        else:
            values = item.get("values") or [{}]
            value = values[-1].get("value")
        if isinstance(value, (int, float)):
            result[ours] = float(value) if ours in RATES else int(value)
    return result
