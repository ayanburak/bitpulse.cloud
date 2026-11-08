"""
file: reels/blocks/__init__.py
importable: Block, KINDS, read_block

Every kind of block the edit file may use, by the name it is written under. A block is written as
a mapping with exactly one key, the kind, for example {card: {...}}.

description: Knows every block kind and reads one block from the edit file.
"""

from typing import Any

from reels.blocks.base import Block, Sources
from reels.blocks.card import Card, Closing
from reels.blocks.document import Document
from reels.blocks.montage import Montage
from reels.blocks.speech import Speech
from reels.fields import CutError

KINDS: dict[str, type[Block]] = {kind.kind: kind for kind in (Speech, Card, Montage, Document, Closing)}


def read_block(item: Any, where: str, sources: Sources) -> Block:
    """Reads one block of the edit file.

    Raises:
        CutError: The block has no single kind, an unknown kind or a field that breaks a rule.
    """
    if not isinstance(item, dict) or len(item) != 1:
        raise CutError(f"{where}: a block is one kind with its fields, for example card: {{...}}")
    kind, data = next(iter(item.items()))
    if kind not in KINDS:
        raise CutError(f"{where}: unknown block {kind}, the blocks are {', '.join(KINDS)}")
    return KINDS[kind].parse(data, f"{where}, {kind}", sources)
