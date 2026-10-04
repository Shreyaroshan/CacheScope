"""Memory-trace parsing and deterministic synthetic generators."""

from __future__ import annotations

import random
from collections.abc import Iterable, Iterator
from pathlib import Path

from .models import Access


def sequential(count: int, *, start: int = 0, step: int = 1) -> Iterator[Access]:
    _validate_generation(count, start, step)
    for index in range(count):
        yield Access(start + index * step)


def strided(count: int, *, start: int = 0, stride: int = 64) -> Iterator[Access]:
    _validate_generation(count, start, stride)
    for index in range(count):
        yield Access(start + index * stride)


def random_addresses(
    count: int, *, maximum_address: int = 4095, seed: int = 0
) -> Iterator[Access]:
    if count < 0:
        raise ValueError("count cannot be negative")
    if maximum_address < 0:
        raise ValueError("maximum_address cannot be negative")
    generator = random.Random(seed)
    for _ in range(count):
        yield Access(generator.randint(0, maximum_address))


def parse_trace(path: str | Path) -> Iterator[Access]:
    """Parse lines formatted as `ADDRESS` or `R|W ADDRESS`.

    Addresses may be decimal or use Python-style prefixes such as `0x`.
    Blank lines and text after `#` are ignored.
    """

    with Path(path).open(encoding="utf-8") as stream:
        yield from parse_trace_lines(stream)


def parse_trace_lines(lines: Iterable[str]) -> Iterator[Access]:
    """Parse trace lines supplied by a file, upload, or in-memory editor."""

    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.partition("#")[0].strip()
        if not line:
            continue
        fields = line.replace(",", " ").split()
        try:
            if len(fields) == 1:
                yield Access(int(fields[0], 0))
            elif len(fields) == 2:
                yield Access(int(fields[1], 0), fields[0].upper())
            else:
                raise ValueError("expected ADDRESS or OPERATION ADDRESS")
        except ValueError as error:
            raise ValueError(
                f"invalid trace line {line_number}: {raw_line.rstrip()}"
            ) from error


def _validate_generation(count: int, start: int, increment: int) -> None:
    if count < 0:
        raise ValueError("count cannot be negative")
    if start < 0:
        raise ValueError("start cannot be negative")
    if increment <= 0:
        raise ValueError("step or stride must be positive")
