"""Command-line interface for CacheScope."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

from .models import Access, CacheConfig
from .experiments import results_to_csv, run_experiments, write_csv
from .simulator import CacheSimulator
from .traces import parse_trace, random_addresses, sequential, strided


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachescope",
        description="Simulate CPU-cache behavior for a file or synthetic trace.",
    )
    parser.add_argument("--cache-size", type=int, default=1024, help="cache bytes")
    parser.add_argument("--block-size", type=int, default=64, help="block bytes")
    parser.add_argument("--associativity", type=int, default=1, help="lines per set")
    parser.add_argument("--policy", choices=("lru", "fifo"), default="lru")
    parser.add_argument("--hit-time", type=float, default=1.0)
    parser.add_argument("--miss-penalty", type=float, default=100.0)

    source = parser.add_mutually_exclusive_group()
    source.add_argument("--trace", type=Path, help="trace file containing ADDRESS or R/W ADDRESS")
    source.add_argument(
        "--pattern", choices=("sequential", "strided", "random"), default="sequential"
    )
    parser.add_argument("--count", type=int, default=1000, help="synthetic access count")
    parser.add_argument("--start", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--step", type=int, default=1, help="sequential byte step")
    parser.add_argument("--stride", type=int, default=64, help="strided byte distance")
    parser.add_argument("--max-address", type=lambda value: int(value, 0), default=4095)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--compare-cache-sizes",
        help="comma-separated cache sizes; enables batch comparison",
    )
    parser.add_argument("--compare-block-sizes", help="comma-separated block sizes")
    parser.add_argument(
        "--compare-associativities", help="comma-separated associativities"
    )
    parser.add_argument(
        "--compare-policies", default="lru,fifo", help="comma-separated policies"
    )
    parser.add_argument("--csv", type=Path, help="write batch comparison results")
    return parser


def _accesses(args: argparse.Namespace) -> Iterable[Access]:
    if args.trace:
        return parse_trace(args.trace)
    if args.pattern == "strided":
        return strided(args.count, start=args.start, stride=args.stride)
    if args.pattern == "random":
        return random_addresses(
            args.count, maximum_address=args.max_address, seed=args.seed
        )
    return sequential(args.count, start=args.start, step=args.step)


def _text_report(config: CacheConfig, stats: dict[str, int | float]) -> str:
    return "\n".join(
        [
            "CacheScope simulation",
            f"  geometry: {config.cache_size} B, {config.block_size} B blocks, "
            f"{config.associativity}-way, {config.number_of_sets} sets",
            f"  policy: {config.policy.upper()}",
            f"  accesses: {stats['accesses']} ({stats['reads']} reads, {stats['writes']} writes)",
            f"  hits / misses: {stats['hits']} / {stats['misses']}",
            f"  hit rate: {stats['hit_rate']:.2%}",
            f"  miss rate: {stats['miss_rate']:.2%}",
            "  miss classes: "
            f"{stats['compulsory_misses']} compulsory, "
            f"{stats['conflict_misses']} conflict, "
            f"{stats['capacity_misses']} capacity",
            f"  evictions / writebacks: {stats['evictions']} / {stats['writebacks']}",
            f"  AMAT: {stats['amat']:.3f}",
        ]
    )


def _integer_list(value: str | None, default: int) -> list[int]:
    if value is None:
        return [default]
    try:
        values = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise ValueError("comparison values must be comma-separated integers") from error
    if not values:
        raise ValueError("comparison list cannot be empty")
    return values


def _comparison_report(results) -> str:
    headings = "cache  block  ways  policy  hit rate  miss rate  AMAT"
    rows = [headings, "-" * len(headings)]
    rows.extend(
        f"{item.cache_size:>5}  {item.block_size:>5}  "
        f"{item.associativity:>4}  {item.policy.upper():>6}  "
        f"{item.hit_rate:>8.2%}  {item.miss_rate:>9.2%}  {item.amat:>6.2f}"
        for item in results
    )
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = CacheConfig(
            cache_size=args.cache_size,
            block_size=args.block_size,
            associativity=args.associativity,
            policy=args.policy,
            hit_time=args.hit_time,
            miss_penalty=args.miss_penalty,
        )
        accesses = list(_accesses(args))
        if args.compare_cache_sizes:
            policies = [item.strip().lower() for item in args.compare_policies.split(",")]
            if not policies or any(item not in {"lru", "fifo"} for item in policies):
                raise ValueError("comparison policies must be lru or fifo")
            results = run_experiments(
                accesses,
                cache_sizes=_integer_list(args.compare_cache_sizes, config.cache_size),
                block_sizes=_integer_list(args.compare_block_sizes, config.block_size),
                associativities=_integer_list(
                    args.compare_associativities, config.associativity
                ),
                policies=policies,
                hit_time=config.hit_time,
                miss_penalty=config.miss_penalty,
            )
            if not results:
                raise ValueError("no valid comparison configurations")
            if args.csv:
                write_csv(results, args.csv)
            if args.format == "json":
                print(json.dumps([item.to_dict() for item in results], indent=2))
            else:
                print(_comparison_report(results))
                if args.csv:
                    print(f"\nCSV written to {args.csv}")
            return 0
        simulator = CacheSimulator(config)
        stats = simulator.run(accesses).to_dict(config.hit_time, config.miss_penalty)
    except (OSError, ValueError) as error:
        raise SystemExit(f"cachescope: error: {error}") from error

    if args.format == "json":
        print(json.dumps({"config": asdict(config), "stats": stats}, indent=2))
    else:
        print(_text_report(config, stats))
    return 0
