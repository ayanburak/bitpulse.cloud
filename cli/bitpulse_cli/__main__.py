"""
file: bitpulse_cli/__main__.py
importable: main, push_draft, publish, pull, pull_all, handle_of, list_rows, days_left, number_of, save_brief,
            candidate_rows, upload_social, link_skills, BRIEFS

    bitpulse setup                      stores the device key, checks the connection and links the skills
    bitpulse setup --skills             only links the skills of this repository
    bitpulse whoami                     shows this device and when its key ends
    bitpulse list                       lists every story
    bitpulse show <handle>              shows one story
    bitpulse history <handle>           lists the versions of one story
    bitpulse job <id>                   shows one publishing job
    bitpulse candidates                 lists the radar events chosen for writing
    bitpulse brief <R-number>           saves the brief of one event and prints where
    bitpulse draft <story folder>       stores the folder as a new draft version
    bitpulse publish <story folder>     stores it, publishes it and renames the folder to its key
    bitpulse social <post folder>       uploads the finished social files of a story
    bitpulse pull <folder> <handle>     copies one story into folder
    bitpulse pull <folder> --all        copies every published story into folder
    bitpulse rebuild                    builds the site again, for example after a code release

draft and publish take --candidate R-0493 to tie the story to the radar event it was written from.

description: The command for uploading, publishing and fetching stories from a device.
"""

# NOTE: A story folder has the same four files as before: en.md, tr.md, image.jpg and social.yaml.
# Pulling every story into site/src/content/stories keeps the local build and the social scripts
# working without knowing the stories now live on the server.
#
# NOTE: There is no command to withdraw a story, undo a publish or make a key. Those need the panel
# and a passkey, so a device key that leaks can not do them.

import argparse
import base64
import getpass
import hashlib
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .client import Api, ApiError, read_key, tunnel, write_key

# --- Constants ---

JOB_WAIT_SECONDS = 180
DATED = re.compile(r"^\d{4}-\d{2}-\d{2}-")
TIME_FORMAT = "%Y-%m-%d %H:%M"
KEY_WARNING_DAYS = 14
BRIEFS = Path.home() / ".cache" / "bitpulse-radar" / "briefs"
SOCIAL_FILE = re.compile(r"^(x\.txt|caption\.txt|post\.mp4|page-\d+\.png)$")

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


def push_draft(api: Api, folder: Path, candidate: Optional[int] = None) -> int:
    """Stores a story folder as a new draft version.

    Args:
        api: API client.
        folder: Story folder.
        candidate: Number of the radar event the story was written from.

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
    if candidate is not None:
        body["candidate"] = candidate
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
def publish(api: Api, folder: Path, candidate: Optional[int] = None) -> dict:
    """Stores a story, publishes it and waits for the result.

    Args:
        api: API client.
        folder: Story folder. It ends up renamed to the published key.
        candidate: Number of the radar event the story was written from.

    Returns:
        Finished job, with the story folder added under the folder key.

    Raises:
        ApiError: If the API refuses the story or the job fails.
    """
    folder = folder.resolve()
    push_draft(api, folder, candidate)
    handle = handle_of(folder)
    job = _wait_for(api, int(api.send_json("POST", f"/stories/{handle}/publish", {})["job"]))
    if job["status"] != "succeeded":
        raise ApiError(0, f"publishing failed, the live site did not change: {job['error']}")
    final = pull(api, folder.parent, handle)
    if final != folder:
        shutil.rmtree(folder)
    return {**job, "folder": str(final)}

# --- Radar ---

def number_of(text: str) -> int:
    """Reads the number of a radar event.

    Args:
        text: R-0493 or plain 493.

    Returns:
        The number.

    Raises:
        ValueError: If the text is neither.
    """
    return int(text.upper().removeprefix("R-"))


def save_brief(api: Api, number: int, folder: Path = BRIEFS) -> Path:
    """Saves the brief of one radar event for a writing session.

    Args:
        api: API client.
        number: Event number.
        folder: Where to save it.

    Returns:
        Path of the saved file.

    Raises:
        ApiError: If the event has no brief yet.
    """
    answer = api.get(f"/candidates/{number}/brief")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"R-{number:04d}.md"
    path.write_text(answer["text"], encoding="utf-8")
    return path


def candidate_rows(items: list[dict]) -> list[str]:
    """Formats the chosen events for the screen.

    Args:
        items: Items from the API.

    Returns:
        One line per event.
    """
    return [f"R-{item['number']:04d}  {'brief ready' if item['has_brief'] else 'no brief   '}  {item['title']}" for item in items]

# --- Social ---

def upload_social(api: Api, folder: Path) -> list[str]:
    """Uploads the finished social files of a story.

    Args:
        api: API client.
        folder: Post folder, named after the story. Anything but the finished files is left out.

    Returns:
        The file names the server stored.

    Raises:
        ApiError: If the API refuses them.
    """
    files = {path.name: base64.b64encode(path.read_bytes()).decode() for path in folder.iterdir() if SOCIAL_FILE.match(path.name)}
    return list(api.send_json("PUT", f"/stories/{handle_of(folder)}/social", {"files": files})["files"])

# --- Skills ---

def _repository() -> Optional[Path]:
    for folder in [Path.cwd(), *Path.cwd().parents]:
        if (folder / "workflows").is_dir() and (folder / "api").is_dir():
            return folder
    return None


# Links are relative so the repository can move, and anything else at the path is left for a person.
def link_skills(root: Path) -> list[str]:
    """Links every workflow of a repository into the skill folder of Claude Code.

    Args:
        root: Repository folder.

    Returns:
        Names of the linked skills.

    Raises:
        OSError: If something other than the right link is already at a skill path.
    """
    skills = root / ".claude" / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    names = []
    for source in sorted((root / "workflows").glob("*/SKILL.md")):
        name = source.parent.name
        link, wanted = skills / name, f"../../workflows/{name}"
        if link.is_symlink() and os.readlink(link) == wanted:
            names.append(name)
            continue
        if link.exists() or link.is_symlink():
            raise OSError(f"{link} already exists, move it away first")
        link.symlink_to(wanted, target_is_directory=True)
        names.append(name)
    return names

# --- Reading ---

def list_rows(stories: list[dict]) -> list[str]:
    """Formats the story list for the screen.

    Args:
        stories: Items from the API.

    Returns:
        One line per story.
    """
    return [f"{item['published_at'] or 'not published':<17}  {item['handle']}  v{item['latest']}" for item in stories]


def days_left(expires_at: str, now: datetime) -> int:
    """Counts the days a key still works.

    Args:
        expires_at: End of the key as YYYY-MM-DD HH:MM in UTC.
        now: Current moment in UTC.

    Returns:
        Whole days, negative once it has ended.
    """
    return (datetime.strptime(expires_at, TIME_FORMAT).replace(tzinfo=timezone.utc) - now).days


def _whoami(api: Api) -> None:
    me = api.get("/whoami")
    left = days_left(me["expires_at"], datetime.now(timezone.utc))
    print(f"device: {me['name']}")
    print(f"key ends: {me['expires_at']} UTC, {left} days left")
    if left <= KEY_WARNING_DAYS:
        print("make a new key in the panel soon")

# --- Commands ---

# The key is typed at a hidden prompt, an argument would stay in the shell history.
def _setup(skills_only: bool) -> None:
    if not skills_only:
        write_key(getpass.getpass("Device key: "))
        with tunnel() as base:
            _whoami(Api(base, read_key()))
    root = _repository()
    if root is not None:
        print(f"skills linked: {', '.join(link_skills(root))}")
    elif skills_only:
        raise OSError("run this inside the repository")


def _finish_job(job: dict, failed: str) -> None:
    if job["status"] != "succeeded":
        raise ApiError(0, f"{failed}, the live site did not change: {job['error']}")
    print(f"live: {job['release']}, {job['duration_ms']} ms")


def _show(api: Api, handle: str) -> None:
    story = api.get(f"/stories/{handle}")
    for name in ("handle", "key", "published_at", "version", "image"):
        print(f"{name}: {story[name]}")


def _job(api: Api, job_id: int) -> None:
    job = api.get(f"/jobs/{job_id}")
    for name in ("id", "kind", "handle", "status", "release", "error", "duration_ms"):
        print(f"{name}: {job[name]}")


def _run(args: argparse.Namespace) -> None:
    candidate = number_of(args.candidate) if getattr(args, "candidate", None) else None
    with tunnel() as base:
        api = Api(base, read_key())
        if args.command == "draft":
            print(f"draft version {push_draft(api, Path(args.folder), candidate)}")
        elif args.command == "candidates":
            print("\n".join(candidate_rows(api.get("/candidates"))) or "nothing is waiting")
        elif args.command == "brief":
            print(save_brief(api, number_of(args.number)))
        elif args.command == "social":
            print(f"uploaded: {', '.join(upload_social(api, Path(args.folder).resolve()))}")
        elif args.command == "publish":
            job = publish(api, Path(args.folder), candidate)
            print(f"live: {job['release']}, {job['duration_ms']} ms")
            print(f"folder: {job['folder']}")
        elif args.command == "pull" and args.all:
            print(f"pulled {pull_all(api, Path(args.folder))} stories")
        elif args.command == "pull":
            if not args.handle:
                raise ApiError(0, "give a story name or --all")
            print(f"pulled to {pull(api, Path(args.folder), args.handle)}")
        elif args.command == "whoami":
            _whoami(api)
        elif args.command == "list":
            print("\n".join(list_rows(api.get("/stories"))))
        elif args.command == "show":
            _show(api, args.handle)
        elif args.command == "history":
            for row in api.get(f"/stories/{args.handle}/versions"):
                print(f"v{row['number']}  {row['created_at']}  {row['actor']}")
        elif args.command == "job":
            _job(api, args.id)
        else:
            _finish_job(_wait_for(api, int(api.send_json("POST", "/rebuild", {"go_live": True})["job"])), "rebuild failed")


def main() -> None:
    """Runs the command given on the command line."""
    parser = argparse.ArgumentParser(prog="bitpulse")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup").add_argument("--skills", action="store_true")
    commands.add_parser("whoami")
    commands.add_parser("list")
    commands.add_parser("show").add_argument("handle")
    commands.add_parser("history").add_argument("handle")
    commands.add_parser("job").add_argument("id", type=int)
    commands.add_parser("candidates")
    commands.add_parser("brief").add_argument("number")
    commands.add_parser("social").add_argument("folder")
    for name in ("draft", "publish"):
        store = commands.add_parser(name)
        store.add_argument("folder")
        store.add_argument("--candidate")
    fetch = commands.add_parser("pull")
    fetch.add_argument("folder")
    fetch.add_argument("handle", nargs="?")
    fetch.add_argument("--all", action="store_true")
    commands.add_parser("rebuild")
    args = parser.parse_args()
    try:
        _setup(args.skills) if args.command == "setup" else _run(args)
    except (ApiError, OSError, ValueError) as error:
        sys.exit(f"error: {error}")


if __name__ == "__main__":
    main()
