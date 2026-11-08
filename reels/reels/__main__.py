"""
file: reels/__main__.py
importable: main

The reels command. Every subcommand prints a few short lines and writes the full result to
files, because its output is read by a model and every line it prints costs.

    reels prep 2026-11-07-iran-nuclear-reward
    reels gather 2026-11-07-iran-nuclear-reward
    reels screen 2026-11-07-iran-nuclear-reward
    reels screen 2026-11-07-iran-nuclear-reward --join
    reels fetch 2026-11-07-iran-nuclear-reward Y1 --from 190 --to 270 --name palm
    reels transcript 2026-11-07-iran-nuclear-reward src/palm.mp4
    reels beats "Inspiring - The_Mountain.mp3" --from 12.7
    reels render examples/2026-11-07-iran-nuclear-reward.yaml
    reels deliver examples/2026-11-07-iran-nuclear-reward.yaml
    reels usage 2026-11-07-iran-nuclear-reward
    reels clean 2026-11-07-iran-nuclear-reward

description: Command line entry point of bitpulse-reels.
"""

import argparse
import sys
import time
from pathlib import Path

from reels.beats import beats
from reels.collect.gather import fetch, gather
from reels.collect.screen import join, prepare
from reels.collect.story import dossier, quotes, read_story
from reels.config import WORK
from reels.cut import load
from reels.deliver import clean, deliver, recent
from reels.fields import CutError
from reels.media import MediaError
from reels.pace import measure as measure_pace
from reels.render import render
from reels.transcript import save, transcribe
from reels.usage import measure, record

# Below this the strength hardly repeats at the found tempo and the grid is a guess.
WEAK_BEAT = 0.3


# The last reels are printed with the dossier, so the model sees what to avoid repeating in the
# same read.
def run_prep(args: argparse.Namespace) -> None:
    story = read_story(args.story)
    work = WORK / args.story
    work.mkdir(parents=True, exist_ok=True)
    out = work / "dossier.md"
    out.write_text(dossier(story))
    print(f"{out}: {len(quotes(story))} quotes, {len(story.sources)} sources")
    print(f"last reels:\n{recent()}")


def run_deliver(args: argparse.Namespace) -> None:
    print(deliver(load(Path(args.cut)), Path(args.cut)))


def run_clean(args: argparse.Namespace) -> None:
    freed = clean(args.story, WORK / args.story)
    print(f"deleted {WORK / args.story}, {freed / 1e6:.0f} MB")


def run_usage(args: argparse.Namespace) -> None:
    path, found = measure(args.session)
    for who, usage in found.items():
        tokens = usage.tokens
        print(f"{who}: {usage.turns} turns, input {tokens['input']}, cache write {tokens['cache_write']}, "
              f"cache read {tokens['cache_read']}, output {tokens['output']}")
    print(f"recorded in {record(args.story, path, found)}, session {path.stem[:8]}")


# The beat is printed in seconds of the reel. A weak beat is said so, the hits are then the only
# times worth cutting on.
def run_beats(args: argparse.Namespace) -> None:
    found = beats(args.track, args.start, args.seconds)
    print(f"{found.tempo:.0f} a minute, a beat every {found.step:.2f} s from {found.first:.2f} s, clear {found.clear:.2f}"
          + (", weak beat, cut on the hits" if found.clear < WEAK_BEAT else ""))
    print(f"hits: {' '.join(f'{hit:.2f}' for hit in found.hits)}")


def run_gather(args: argparse.Namespace) -> None:
    began = time.monotonic()
    out = gather(args.story, WORK / args.story, print)
    print(f"{out}, in {time.monotonic() - began:.0f} s")


# The task files are for Haiku. The printed line tells the model what to start, nothing more.
def run_screen(args: argparse.Namespace) -> None:
    work = WORK / args.story
    if args.join:
        print(join(work))
        return
    tasks = prepare(args.story, work)
    print(f"{len(tasks)} tasks, start one Haiku agent per file with the prompt: Read <file> and do what it says.")
    for task in tasks:
        print(task)


def run_fetch(args: argparse.Namespace) -> None:
    path, note = fetch(WORK / args.story, args.id, args.start, args.end, args.name)
    print(f"{path.relative_to(WORK / args.story)}: {note}")


# A transcript is saved next to the sources, under the file's own name, so a voice in any edit
# file finds it by the file it plays.
def run_transcript(args: argparse.Namespace) -> None:
    work = WORK / args.story
    for name in args.files:
        source = work / name
        if not source.is_file():
            raise CutError(f"no file {source}")
        began = time.monotonic()
        transcript = transcribe(source)
        readable = save(transcript, work / "transcripts" / f"{source.stem}.json")
        print(f"{readable}: {len(transcript.words)} words, {time.monotonic() - began:.0f} s")


def run_render(args: argparse.Namespace) -> None:
    began = time.monotonic()
    cut = load(Path(args.cut))
    pace = measure_pace(cut.blocks, music=cut.music is not None)
    for warning in [*cut.warnings, *pace.warnings()]:
        print(f"warning: {warning}")
    result = render(cut)
    print(f"reel: {result.reel}")
    print(f"sheet: {result.sheet}")
    print(f"length {result.seconds:.2f} s, loudness {result.loudness:.1f} LUFS, rendered in {time.monotonic() - began:.0f} s")
    print(f"black cards {pace.black:.1f} s, {pace.share:.0%} of the reel")


def main() -> None:
    parser = argparse.ArgumentParser(prog="reels", description="Cuts Instagram reels for Bitpulse news stories.")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("prep", help="write the dossier of a story, the first thing to read")
    command.add_argument("story", help="story folder name")
    command.set_defaults(handler=run_prep)
    command = commands.add_parser("gather", help="gather candidates by the plan.yaml in the story's work folder")
    command.add_argument("story", help="story folder name")
    command.set_defaults(handler=run_gather)
    command = commands.add_parser("screen", help="write Haiku's screening tasks, or join its notes with --join")
    command.add_argument("story", help="story folder name")
    command.add_argument("--join", action="store_true", help="join the notes into candidates.md")
    command.set_defaults(handler=run_screen)
    command = commands.add_parser("fetch", help="bring a gathered candidate into the sources")
    command.add_argument("story", help="story folder name")
    command.add_argument("id", help="the candidate's id in gathered.md, for example Y3")
    command.add_argument("--from", dest="start", type=float, help="first second to keep of a YouTube video")
    command.add_argument("--to", dest="end", type=float, help="last second to keep of a YouTube video")
    command.add_argument("--name", required=True, help="the source's file name, without extension")
    command.set_defaults(handler=run_fetch)
    command = commands.add_parser("transcript", help="write down the words of sources with their times")
    command.add_argument("story", help="story folder name")
    command.add_argument("files", nargs="+", help="files in the story's work folder, for example src/palm.mp4")
    command.set_defaults(handler=run_transcript)
    command = commands.add_parser("deliver", help="put the rendered reel and its caption next to the story's post")
    command.add_argument("cut", help="path of the cut.yaml file")
    command.set_defaults(handler=run_deliver)
    command = commands.add_parser("clean", help="delete a story's raw material after its reel is delivered")
    command.add_argument("story", help="story folder name")
    command.set_defaults(handler=run_clean)
    command = commands.add_parser("usage", help="count the tokens of a reels session and record them")
    command.add_argument("story", help="story folder name")
    command.add_argument("--session", help="session id, the newest session when left out")
    command.set_defaults(handler=run_usage)
    command = commands.add_parser("beats", help="the beat and the hits of a library track, in seconds of the reel")
    command.add_argument("track", help="file name in library/music")
    command.add_argument("--from", dest="start", type=float, required=True, help="the music's from in the edit file")
    command.add_argument("--seconds", type=float, default=45, help="how much of the track to read")
    command.set_defaults(handler=run_beats)
    command = commands.add_parser("render", help="render the reel of an edit file")
    command.add_argument("cut", help="path of the cut.yaml file")
    command.set_defaults(handler=run_render)
    args = parser.parse_args()
    try:
        args.handler(args)
    except (CutError, MediaError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
