"""Batch comparison and export utilities for CacheScope experiments."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import Access, CacheConfig
from .simulator import CacheSimulator


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    cache_size: int
    block_size: int
    associativity: int
    number_of_sets: int
    policy: str
    accesses: int
    hits: int
    misses: int
    compulsory_misses: int
    conflict_misses: int
    capacity_misses: int
    evictions: int
    writebacks: int
    hit_rate: float
    miss_rate: float
    amat: float

    def to_dict(self) -> dict[str, int | float | str]:
        return asdict(self)


def run_experiments(
    accesses: Iterable[Access | int],
    *,
    cache_sizes: Sequence[int],
    block_sizes: Sequence[int],
    associativities: Sequence[int],
    policies: Sequence[str] = ("lru", "fifo"),
    hit_time: float = 1.0,
    miss_penalty: float = 100.0,
) -> list[ExperimentResult]:
    """Run every valid configuration over the same materialized trace."""

    trace = list(accesses)
    results: list[ExperimentResult] = []
    for cache_size in cache_sizes:
        for block_size in block_sizes:
            for associativity in associativities:
                for policy in policies:
                    try:
                        config = CacheConfig(
                            cache_size=cache_size,
                            block_size=block_size,
                            associativity=associativity,
                            policy=policy,  # type: ignore[arg-type]
                            hit_time=hit_time,
                            miss_penalty=miss_penalty,
                        )
                    except ValueError:
                        continue
                    stats = CacheSimulator(config).run(trace)
                    results.append(
                        ExperimentResult(
                            cache_size=config.cache_size,
                            block_size=config.block_size,
                            associativity=config.associativity,
                            number_of_sets=config.number_of_sets,
                            policy=config.policy,
                            accesses=stats.accesses,
                            hits=stats.hits,
                            misses=stats.misses,
                            compulsory_misses=stats.compulsory_misses,
                            conflict_misses=stats.conflict_misses,
                            capacity_misses=stats.capacity_misses,
                            evictions=stats.evictions,
                            writebacks=stats.writebacks,
                            hit_rate=stats.hit_rate,
                            miss_rate=stats.miss_rate,
                            amat=stats.amat(hit_time, miss_penalty),
                        )
                    )
    return results


def results_to_csv(results: Sequence[ExperimentResult]) -> str:
    """Serialize experiment results to CSV text."""

    if not results:
        return ""
    from io import StringIO

    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(results[0].to_dict()))
    writer.writeheader()
    writer.writerows(result.to_dict() for result in results)
    return stream.getvalue()


def write_csv(results: Sequence[ExperimentResult], path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(results_to_csv(results), encoding="utf-8", newline="")
    return destination
