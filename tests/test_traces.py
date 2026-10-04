from pathlib import Path

import pytest

from cachescope import Access
from cachescope.traces import parse_trace, random_addresses, sequential, strided


def test_synthetic_patterns() -> None:
    assert list(sequential(4, start=8, step=2)) == [
        Access(8),
        Access(10),
        Access(12),
        Access(14),
    ]
    assert list(strided(3, start=0, stride=64)) == [
        Access(0),
        Access(64),
        Access(128),
    ]


def test_random_pattern_is_reproducible() -> None:
    first = list(random_addresses(10, maximum_address=100, seed=42))
    second = list(random_addresses(10, maximum_address=100, seed=42))

    assert first == second


def test_parse_trace_supports_operations_comments_and_hex(tmp_path: Path) -> None:
    trace = tmp_path / "sample.trace"
    trace.write_text("# sample\nR 0x10\nW, 32\n48 # read\n", encoding="utf-8")

    assert list(parse_trace(trace)) == [Access(16), Access(32, "W"), Access(48)]


def test_parse_trace_reports_line_number(tmp_path: Path) -> None:
    trace = tmp_path / "bad.trace"
    trace.write_text("0\nnot-an-address\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 2"):
        list(parse_trace(trace))
