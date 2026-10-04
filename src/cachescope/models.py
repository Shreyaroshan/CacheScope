"""Data models shared by the simulator, trace parser, and CLI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Operation = Literal["R", "W"]
PolicyName = Literal["lru", "fifo"]


@dataclass(frozen=True, slots=True)
class CacheConfig:
    """Validated cache geometry and timing configuration."""

    cache_size: int
    block_size: int
    associativity: int = 1
    policy: PolicyName = "lru"
    hit_time: float = 1.0
    miss_penalty: float = 100.0

    def __post_init__(self) -> None:
        integer_fields = {
            "cache_size": self.cache_size,
            "block_size": self.block_size,
            "associativity": self.associativity,
        }
        for name, value in integer_fields.items():
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

        if self.cache_size % self.block_size != 0:
            raise ValueError("cache_size must be divisible by block_size")
        if self.number_of_lines % self.associativity != 0:
            raise ValueError(
                "the number of cache lines must be divisible by associativity"
            )
        if self.policy not in {"lru", "fifo"}:
            raise ValueError("policy must be 'lru' or 'fifo'")
        if self.hit_time < 0:
            raise ValueError("hit_time cannot be negative")
        if self.miss_penalty < 0:
            raise ValueError("miss_penalty cannot be negative")

    @property
    def number_of_lines(self) -> int:
        return self.cache_size // self.block_size

    @property
    def number_of_sets(self) -> int:
        return self.number_of_lines // self.associativity


@dataclass(frozen=True, slots=True)
class Access:
    """One byte-addressed memory access."""

    address: int
    operation: Operation = "R"

    def __post_init__(self) -> None:
        if isinstance(self.address, bool) or not isinstance(self.address, int):
            raise ValueError("address must be an integer")
        if self.address < 0:
            raise ValueError("address cannot be negative")
        operation = self.operation.upper()
        if operation not in {"R", "W"}:
            raise ValueError("operation must be 'R' or 'W'")
        object.__setattr__(self, "operation", operation)


@dataclass(frozen=True, slots=True)
class AccessResult:
    """Mapping and outcome for one access."""

    access: Access
    hit: bool
    block: int
    set_index: int
    tag: int
    line_index: int
    evicted_tag: int | None = None
    writeback: bool = False


@dataclass(slots=True)
class SimulationStats:
    """Aggregate counters and derived performance metrics."""

    accesses: int = 0
    reads: int = 0
    writes: int = 0
    hits: int = 0
    misses: int = 0
    compulsory_misses: int = 0
    conflict_misses: int = 0
    capacity_misses: int = 0
    evictions: int = 0
    writebacks: int = 0

    @property
    def hit_rate(self) -> float:
        return self.hits / self.accesses if self.accesses else 0.0

    @property
    def miss_rate(self) -> float:
        return self.misses / self.accesses if self.accesses else 0.0

    def amat(self, hit_time: float, miss_penalty: float) -> float:
        return hit_time + self.miss_rate * miss_penalty

    def to_dict(self, hit_time: float, miss_penalty: float) -> dict[str, int | float]:
        result: dict[str, int | float] = asdict(self)
        result.update(
            hit_rate=self.hit_rate,
            miss_rate=self.miss_rate,
            amat=self.amat(hit_time, miss_penalty),
        )
        return result
