"""
file: reels/fields.py
importable: CutError, record, number, text, crop, centre, Crop

The edit file is written by a model, so every field is checked before anything is rendered and a
mistake names the exact place it was found in, for example "blocks 3, speech, voice: missing to".

description: Reads and checks single fields of the edit file.
"""

from dataclasses import dataclass
from typing import Any


# One error type for every mistake in the edit file, so the command line can print it as one
# short line instead of a traceback.
class CutError(Exception):
    """Raised when the edit file breaks a rule. The message names where."""


@dataclass(frozen=True)
class Crop:
    width: int
    height: int
    x: int
    y: int

    def filter(self) -> str:
        return f"crop={self.width}:{self.height}:{self.x}:{self.y}"


def record(value: Any, where: str, allowed: set[str]) -> dict[str, Any]:
    """Returns value as a mapping after checking that it holds no unknown field.

    Args:
        value: The raw YAML value.
        where: Where the value sits in the file, used in the error.
        allowed: Field names the mapping may hold.

    Raises:
        CutError: value is not a mapping or holds a field outside allowed.
    """
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise CutError(f"{where}: expected a mapping")
    unknown = set(value) - allowed
    if unknown:
        raise CutError(f"{where}: unknown field {sorted(unknown)[0]}")
    return value


def number(data: dict[str, Any], key: str, where: str, low: float, high: float, default: float | None = None) -> float:
    """Returns a number field that lies between low and high.

    Args:
        data: The mapping that holds the field.
        key: Field name.
        where: Where the mapping sits in the file, used in the error.
        low: Smallest allowed value.
        high: Largest allowed value.
        default: Value when the field is missing. Without it the field is required.

    Raises:
        CutError: The field is missing without a default, is not a number or is out of range.
    """
    value = data.get(key, default)
    if value is None:
        raise CutError(f"{where}: missing {key}")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CutError(f"{where}: {key} must be a number")
    if not low <= value <= high:
        raise CutError(f"{where}: {key} is {value}, it must be between {low} and {high}")
    return float(value)


def text(data: dict[str, Any], key: str, where: str) -> str:
    """Returns a required text field with its outer spaces removed.

    Raises:
        CutError: The field is missing, empty or not text.
    """
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CutError(f"{where}: missing {key}")
    return value.strip()


# The widest 9:16 window in the middle of a source, for a shot whose crop is left out.
def centre(width: int, height: int) -> Crop:
    if width * 16 >= height * 9:
        cut = height * 9 // 16
        return Crop(cut, height, (width - cut) // 2, 0)
    cut = width * 16 // 9
    return Crop(width, cut, 0, (height - cut) // 2)


# A crop must keep the 9:16 shape of the frame, otherwise the picture is stretched when it is
# scaled to 1080 by 1920. A pixel of rounding is allowed, 405:720 is not exactly 9:16.
def crop(value: Any, where: str) -> Crop:
    """Reads a crop written as width:height:x:y in pixels of the source.

    Raises:
        CutError: The value is not four whole numbers or is not close to 9:16.
    """
    parts = str(value).split(":")
    if len(parts) != 4 or not all(part.isdigit() for part in parts):
        raise CutError(f"{where}: crop must be width:height:x:y in pixels, got {value}")
    width, height, x, y = (int(part) for part in parts)
    if width == 0 or abs(width * 16 / 9 - height) > 2:
        raise CutError(f"{where}: crop {value} is not 9:16, the height for width {width} is {round(width * 16 / 9)}")
    return Crop(width, height, x, y)
