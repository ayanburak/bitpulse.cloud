"""
file: bitpulse_api/content.py
importable: InvalidDraft, parse_file, parse_draft, to_markdown, stamp_updates, handle_of, HANDLE

A draft arrives as the same en.md and tr.md text the editor works on. parse_draft checks it and
turns it into plain data for the database. to_markdown writes that data back as the file the site
build reads.

description: Checks story text and converts it between Markdown files and stored data.
"""

# NOTE: These checks exist to refuse a bad draft early and with a clear message. The site build in
# site/src/stories.ts still validates every story again, so a rule missing here can not put a
# broken page on the live site.
#
# XXX: The date and time written in a draft are ignored on purpose. The server sets the publishing
# moment, otherwise a story written in the morning and published at night sinks on the home page.

import re
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator

# --- Constants ---

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
HANDLE = re.compile(SLUG)
DATED = re.compile(r"^\d{4}-\d{2}-\d{2}-")
MOMENT_FORMAT = "%Y-%m-%d %H:%M"

# --- Errors ---

# One error type for every kind of bad draft, the HTTP layer turns it into a single response.
class InvalidDraft(Exception):
    """Raised when story text can not be accepted. The message says what is wrong."""

# --- Models ---

# A shared base refuses unknown fields, so a misspelled field fails instead of being dropped.
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)


# Pydantic only checks the address. The original text is kept, so stored links stay byte for byte.
class Source(_Strict):
    name: str
    url: str

    @field_validator("url")
    @classmethod
    def _http(cls, value: str) -> str:
        HttpUrl(value)
        return value


class Image(_Strict):
    file: str
    alt: str
    credit: str
    license: str
    licenseUrl: str
    source: str

    @field_validator("licenseUrl", "source")
    @classmethod
    def _http(cls, value: str) -> str:
        HttpUrl(value)
        return value


# An update without a time is a new one, the server stamps it during publishing.
class Update(_Strict):
    time: Optional[str] = None
    note: str
    promote: bool = False


class Language(_Strict):
    slug: str = Field(pattern=SLUG)
    title: str
    summary: str
    category: Literal["world", "economy", "technology", "science", "health", "culture", "sports"]
    kind: Literal["news", "long"]
    sources: list[Source] = Field(min_length=1)
    image: Image
    updates: list[Update] = []
    corrected: Optional[str] = None

# --- Parsing ---

# YAML turns an unquoted date or clock into something other than text, so times are read as text
# only after this check.
def parse_file(raw: str, where: str) -> tuple[dict[str, Any], str, Optional[str], Optional[str]]:
    """Reads one story file.

    Args:
        raw: Whole text of en.md or tr.md.
        where: Name used in error messages.

    Returns:
        Checked fields, the Markdown body, then the date and time written in the file.

    Raises:
        InvalidDraft: If the file is malformed or a field is missing or wrong.
    """
    parts = FRONTMATTER.match(raw.replace("\r\n", "\n"))
    if not parts:
        raise InvalidDraft(f"{where}: missing frontmatter")
    if not parts[2].strip():
        raise InvalidDraft(f"{where}: empty body")
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as error:
        raise InvalidDraft(f"{where}: invalid frontmatter") from error
    if not isinstance(data, dict):
        raise InvalidDraft(f"{where}: invalid frontmatter")

    date = data.pop("date", None)
    clock = data.pop("time", None)
    try:
        fields = Language.model_validate(data).model_dump()
    except ValidationError as error:
        first = error.errors()[0]
        path = ".".join(str(item) for item in first["loc"])
        raise InvalidDraft(f"{where}: {path}: {first['msg']}") from None
    return fields, parts[2], None if date is None else str(date), None if clock is None else str(clock)


# Facts shared by both languages must match, otherwise one reader sees a different story.
def _check_pair(en: dict[str, Any], tr: dict[str, Any]) -> None:
    for field in ("category", "kind", "corrected"):
        if en[field] != tr[field]:
            raise InvalidDraft(f"{field} differs between languages")
    if [(u["time"], u["promote"]) for u in en["updates"]] != [(u["time"], u["promote"]) for u in tr["updates"]]:
        raise InvalidDraft("updates differ between languages")


def parse_draft(en: str, tr: str, social: str = "") -> dict[str, Any]:
    """Checks both language files of a draft.

    Args:
        en: Text of en.md.
        tr: Text of tr.md.
        social: Text of social.yaml, stored as it is.

    Returns:
        Plain data that can be stored as JSON.

    Raises:
        InvalidDraft: If either file is invalid or the languages disagree.
    """
    en_fields, en_body, _, _ = parse_file(en, "en.md")
    tr_fields, tr_body, _, _ = parse_file(tr, "tr.md")
    _check_pair(en_fields, tr_fields)
    return {"en": {**en_fields, "body": en_body}, "tr": {**tr_fields, "body": tr_body}, "social": social}


def handle_of(name: str) -> str:
    """Returns the lasting name of a story from its folder name.

    Args:
        name: Folder name, with or without a leading date.

    Returns:
        The folder name without the date.

    Raises:
        InvalidDraft: If what remains can not be used in an address.
    """
    handle = DATED.sub("", name)
    if not HANDLE.match(handle):
        raise InvalidDraft(f"invalid story name: {name}")
    return handle

# --- Writing ---

# Empty optional fields are left out, which is how an editor writes the file by hand.
def to_markdown(version: dict[str, Any], moment: str) -> str:
    """Writes one language of a story as a site build file.

    Args:
        version: One language from the stored content.
        moment: Publishing moment as YYYY-MM-DD HH:MM.

    Returns:
        Text with frontmatter and body.
    """
    date, clock = moment.split(" ")
    fields: dict[str, Any] = {
        "slug": version["slug"],
        "title": version["title"],
        "summary": version["summary"],
        "category": version["category"],
        "date": date,
        "time": clock,
        "kind": version["kind"],
        "sources": version["sources"],
        "image": version["image"],
    }
    if version["updates"]:
        fields["updates"] = version["updates"]
    if version["corrected"]:
        fields["corrected"] = version["corrected"]
    head = yaml.safe_dump(fields, sort_keys=False, allow_unicode=True, width=10_000)
    return f"---\n{head}---\n{version['body']}"

# --- Stamping ---

# The site wants every update strictly after the one before it, and times only have minutes. A
# second update inside the same minute moves one minute forward to stay valid.
def stamp_updates(content: dict[str, Any], published: str, moment: str) -> dict[str, Any]:
    """Gives every new update a time.

    Args:
        content: Stored content of the story.
        published: Publishing moment of the story.
        moment: Current moment as YYYY-MM-DD HH:MM.

    Returns:
        A copy of content where no update is left without a time.
    """
    en = [dict(item) for item in content["en"]["updates"]]
    tr = [dict(item) for item in content["tr"]["updates"]]
    last = datetime.strptime(published, MOMENT_FORMAT)
    now = datetime.strptime(moment, MOMENT_FORMAT)
    for first, second in zip(en, tr):
        if first["time"] is None:
            stamp = max(now, last + timedelta(minutes=1)).strftime(MOMENT_FORMAT)
            first["time"] = second["time"] = stamp
        last = datetime.strptime(first["time"], MOMENT_FORMAT)
    return {**content, "en": {**content["en"], "updates": en}, "tr": {**content["tr"], "updates": tr}}
