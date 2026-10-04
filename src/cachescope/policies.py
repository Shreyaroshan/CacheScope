"""Replacement-policy implementations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class LineState(Protocol):
    valid: bool
    inserted_at: int
    last_used_at: int


def choose_victim(lines: Sequence[LineState], policy: str) -> int:
    """Return the line index to fill or evict."""

    for index, line in enumerate(lines):
        if not line.valid:
            return index

    if policy == "lru":
        return min(range(len(lines)), key=lambda index: lines[index].last_used_at)
    if policy == "fifo":
        return min(range(len(lines)), key=lambda index: lines[index].inserted_at)
    raise ValueError(f"unsupported replacement policy: {policy}")
