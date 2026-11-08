"""
file: reels/collect/sheet.py
importable: tile

description: Lays small frames or images out on one sheet, each with its time or name.
"""

# NOTE: A sheet is looked at by a model, and an image costs by its size. Six columns of 240
# pixels keep a sheet near 1440 pixels wide, enough to see what a frame shows. A sheet of fewer
# images is only as wide as they are, a single Commons picture was paying for five empty cells.

from pathlib import Path

from PIL import Image, ImageDraw

COLUMNS = 6
CELL = 240


def tile(images: list[Path | Image.Image], labels: list[str], out: Path) -> Path | None:
    """Writes the images side by side, six to a row, each with its label, and returns out."""
    if not images:
        return None
    thumbs = []
    for item in images:
        image = item if isinstance(item, Image.Image) else Image.open(item)
        image = image.convert("RGB")
        thumbs.append(image.resize((CELL, max(1, round(image.height * CELL / image.width)))))
    height = max(thumb.height for thumb in thumbs)
    rows = -(-len(thumbs) // COLUMNS)
    sheet = Image.new("RGB", (min(COLUMNS, len(thumbs)) * CELL, rows * height), "black")
    draw = ImageDraw.Draw(sheet)
    for index, (thumb, label) in enumerate(zip(thumbs, labels)):
        x, y = index % COLUMNS * CELL, index // COLUMNS * height
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + 8 * len(label) + 6, y + 16), fill="black")
        draw.text((x + 3, y + 2), label, fill="yellow")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=82)
    return out
