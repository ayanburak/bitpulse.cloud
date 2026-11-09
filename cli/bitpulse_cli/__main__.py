"""
file: bitpulse_cli/__main__.py
importable: main, push_draft, publish, pull, pull_all, handle_of

    bitpulse draft <story folder>       stores the folder as a new draft version
    bitpulse publish <story folder>     stores it, publishes it and renames the folder to its key
    bitpulse pull <folder> <handle>     copies one story into folder
    bitpulse pull <folder> --all        copies every published story into folder
    bitpulse rebuild                    builds the site again, for example after a code release

description: The command for uploading, publishing and fetching stories from a device.
"""

# NOTE: A story folder has the same four files as before: en.md, tr.md, image.jpg and social.yaml.
# Pulling every story into site/src/content/stories keeps the local build and the social scripts
# working without knowing the stories now live on the server.

import argparse
import hashlib
import re
import shutil
import sys
import time
from pathlib import Path

from .client import Api, ApiError, read_key, tunnel

# --- Constants ---

JOB_WAIT_SECONDS = 180
DATED = re.compile(r"^\d{4}-\d{2}-\d{2}-")

# --- Stories ---

def handle_of(folder: Path) -> str:
    """Returns the lasting name of a story from its folder.

    Args:
        folder: Story folder, with or without a date in its name.

    Returns:
        The folder name without the date.
    """
    return DATED.sub("", folder.resolve().name)


# Every upload is rebuilt on the server. An image that came from the server has the same hash, and
# sending it again would only make a slightly worse copy of the same picture.
def _image_hash(api: Api, path: Path) -> str:
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    try:
        api.get_bytes(f"/images/{sha}")
        return sha
    except ApiError as error:
        if error.status != 404:
            raise
    return str(api.post_bytes("/images", data)["sha"])


def push_draft(api: Api, folder: Path) -> int:
    """Stores a story folder as a new draft version.

    Args:
        api: API client.
        folder: Story folder.

    Returns:
        Number of the new version.

    Raises:
        ApiError: If the API refuses the draft.
        OSError: If a required file is missing.
    """
    social = folder / "social.yaml"
    body = {
        "en": (folder / "en.md").read_text(encoding="utf-8"),
        "tr": (folder / "tr.md").read_text(encoding="utf-8"),
        "social": social.read_text(encoding="utf-8") if social.exists() else "",
        "image": _image_hash(api, folder / "image.jpg"),
    }
    return int(api.send_json("PUT", f"/stories/{handle_of(folder)}/draft", body)["version"])


def _wait_for(api: Api, job_id: int) -> dict:
    deadline = time.monotonic() + JOB_WAIT_SECONDS
    while time.monotonic() < deadline:
        job = api.get(f"/jobs/{job_id}")
        if job["status"] in ("succeeded", "failed"):
            return job
        time.sleep(1)
    raise ApiError(0, f"job {job_id} is still running, check it later")


# Explainers are not shared and must have no social file at all, the site tests check for that.
def _write_story(api: Api, root: Path, story: dict) -> Path:
    folder = root / story["key"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "en.md").write_text(story["en"], encoding="utf-8")
    (folder / "tr.md").write_text(story["tr"], encoding="utf-8")
    social = folder / "social.yaml"
    if story["social"]:
        social.write_text(story["social"], encoding="utf-8")
    else:
        social.unlink(missing_ok=True)
    image = folder / "image.jpg"
    if not image.exists() or hashlib.sha256(image.read_bytes()).hexdigest() != story["image"]:
        image.write_bytes(api.get_bytes(f"/images/{story['image']}"))
    return folder


def pull(api: Api, root: Path, handle: str) -> Path:
    """Copies one published story into a folder.

    Args:
        api: API client.
        root: Parent folder.
        handle: Lasting name of the story.

    Returns:
        Folder of the story.

    Raises:
        ApiError: If the story does not exist or was never published.
    """
    story = api.get(f"/stories/{handle}")
    if story["key"] is None:
        raise ApiError(0, f"story was never published: {handle}")
    return _write_story(api, root, story)


def pull_all(api: Api, root: Path) -> int:
    """Copies every published story into a folder.

    Args:
        api: API client.
        root: Parent folder.

    Returns:
        Number of stories copied.
    """
    published = [item for item in api.get("/stories") if item["key"]]
    for item in published:
        pull(api, root, item["handle"])
    return len(published)


# The server decides the date, so the finished story may belong in a folder with another name. The
# new folder is written first and the old one is removed only after that.
def publish(api: Api, folder: Path) -> dict:
    """Stores a story, publishes it and waits for the result.

    Args:
        api: API client.
        folder: Story folder. It ends up renamed to the published key.

    Returns:
        Finished job, with the story folder added under the folder key.

    Raises:
        ApiError: If the API refuses the story or the job fails.
    """
    folder = folder.resolve()
    push_draft(api, folder)
    handle = handle_of(folder)
    job = _wait_for(api, int(api.send_json("POST", f"/stories/{handle}/publish", {})["job"]))
    if job["status"] != "succeeded":
        raise ApiError(0, f"publishing failed, the live site did not change: {job['error']}")
    final = pull(api, folder.parent, handle)
    if final != folder:
        shutil.rmtree(folder)
    return {**job, "folder": str(final)}

# --- Commands ---

def _run(args: argparse.Namespace) -> None:
    with tunnel() as base:
        api = Api(base, read_key())
        if args.command == "draft":
            print(f"draft version {push_draft(api, Path(args.folder))}")
        elif args.command == "publish":
            job = publish(api, Path(args.folder))
            print(f"live: {job['release']}, {job['duration_ms']} ms")
            print(f"folder: {job['folder']}")
        elif args.command == "pull" and args.all:
            print(f"pulled {pull_all(api, Path(args.folder))} stories")
        elif args.command == "pull":
            if not args.handle:
                raise ApiError(0, "give a story name or --all")
            print(f"pulled to {pull(api, Path(args.folder), args.handle)}")
        else:
            job = _wait_for(api, int(api.send_json("POST", "/rebuild", {"go_live": True})["job"]))
            if job["status"] != "succeeded":
                raise ApiError(0, f"rebuild failed, the live site did not change: {job['error']}")
            print(f"live: {job['release']}, {job['duration_ms']} ms")


def main() -> None:
    """Runs the command given on the command line."""
    parser = argparse.ArgumentParser(prog="bitpulse")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("draft").add_argument("folder")
    commands.add_parser("publish").add_argument("folder")
    fetch = commands.add_parser("pull")
    fetch.add_argument("folder")
    fetch.add_argument("handle", nargs="?")
    fetch.add_argument("--all", action="store_true")
    commands.add_parser("rebuild")
    try:
        _run(parser.parse_args())
    except (ApiError, OSError) as error:
        sys.exit(f"error: {error}")


if __name__ == "__main__":
    main()
