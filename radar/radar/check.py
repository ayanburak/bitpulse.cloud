"""
file: radar/check.py
importable: check_story, numbers, quotes

Looks for every number and every quote of a finished English story in the brief it was written
from. Whatever can not be found is printed, so a person or a small model only has to look at
those lines instead of comparing the whole story with every source.

description: Finds numbers and quotes of a story that its brief does not contain.
"""

# NOTE: A miss is not proof of a mistake. A number may be written as a word in the source, or
# come from a source that is not in the brief. It only says where to look.

import re
from pathlib import Path

# --- Patterns ---

FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.S)
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
QUOTE = re.compile(r"[\"“]([^\"”]{12,}?)[\"”]")
YEAR = re.compile(r"^(19|20)\d\d$")


def plain(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).lower()


def numbers(text: str) -> set[str]:
    # Years are left out, they match almost anywhere and almost never carry the mistake.
    found = {match.replace(",", "") for match in NUMBER.findall(text)}
    return {number for number in found if not YEAR.match(number) and len(number) > 1}


def quotes(text: str) -> list[str]:
    return [quote.strip() for quote in QUOTE.findall(text)]


# --- Check ---

def check_story(story: str, brief: str) -> list[str]:
    """
    Lists what the brief does not contain.

    Args:
        story: Text of en.md, with or without its frontmatter.
        brief: Text of the brief file.

    Returns:
        One line per missing number or quote, empty when everything was found.
    """
    body = FRONTMATTER.sub("", story)
    source = plain(brief)
    source_numbers = numbers(brief)
    missing = [f"number not in brief: {number}" for number in sorted(numbers(body)) if number not in source_numbers]
    missing += [f"quote not in brief: {quote}" for quote in quotes(body) if plain(quote) not in source]
    return missing


def check_files(story_path: str, brief_path: str) -> list[str]:
    return check_story(Path(story_path).read_text(encoding="utf-8"), Path(brief_path).read_text(encoding="utf-8"))
