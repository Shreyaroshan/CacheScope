"""Set-associative cache simulation engine."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass

from .models import Access, AccessResult, CacheConfig, SimulationStats
from .policies import choose_victim


@dataclass(slots=True)
class _CacheLine:
    valid: bool = False
    tag: int = 0
    dirty: bool = False
    inserted_at: int = 0
    last_used_at: int = 0


class CacheSimulator:
    """Simulate a write-back, write-allocate CPU cache."""

    def __init__(self, config: CacheConfig) -> None:
        self.config = config
        self._clock = 0
        self._sets = [
            [_CacheLine() for _ in range(config.associativity)]
            for _ in range(config.number_of_sets)
        ]
        self._seen_blocks: set[int] = set()
        self._shadow_lru: OrderedDict[int, None] = OrderedDict()
        self.stats = SimulationStats()

    def reset(self) -> None:
        """Clear cache contents and statistics."""

        self._clock = 0
        self._sets = [
            [_CacheLine() for _ in range(self.config.associativity)]
            for _ in range(self.config.number_of_sets)
        ]
        self._seen_blocks = set()
        self._shadow_lru = OrderedDict()
        self.stats = SimulationStats()

    def map_address(self, address: int) -> tuple[int, int, int]:
        """Return `(block, set_index, tag)` for a byte address."""

        if isinstance(address, bool) or not isinstance(address, int) or address < 0:
            raise ValueError("address must be a non-negative integer")
        block = address // self.config.block_size
        set_index = block % self.config.number_of_sets
        tag = block // self.config.number_of_sets
        return block, set_index, tag

    def access(self, access: Access | int) -> AccessResult:
        """Execute one memory access and return its detailed outcome."""

        if isinstance(access, int) and not isinstance(access, bool):
            access = Access(access)
        if not isinstance(access, Access):
            raise TypeError("access must be an Access instance or integer address")

        self._clock += 1
        self.stats.accesses += 1
        if access.operation == "R":
            self.stats.reads += 1
        else:
            self.stats.writes += 1

        block, set_index, tag = self.map_address(access.address)
        lines = self._sets[set_index]
        shadow_hit = block in self._shadow_lru
        first_access = block not in self._seen_blocks

        for line_index, line in enumerate(lines):
            if line.valid and line.tag == tag:
                line.last_used_at = self._clock
                if access.operation == "W":
                    line.dirty = True
                self.stats.hits += 1
                self._update_shadow_cache(block)
                return AccessResult(
                    access=access,
                    hit=True,
                    block=block,
                    set_index=set_index,
                    tag=tag,
                    line_index=line_index,
                )

        self.stats.misses += 1
        if first_access:
            self.stats.compulsory_misses += 1
        elif shadow_hit:
            self.stats.conflict_misses += 1
        else:
            self.stats.capacity_misses += 1
        line_index = choose_victim(lines, self.config.policy)
        victim = lines[line_index]
        evicted_tag = victim.tag if victim.valid else None
        writeback = victim.valid and victim.dirty
        if victim.valid:
            self.stats.evictions += 1
        if writeback:
            self.stats.writebacks += 1

        victim.valid = True
        victim.tag = tag
        victim.dirty = access.operation == "W"
        victim.inserted_at = self._clock
        victim.last_used_at = self._clock
        self._update_shadow_cache(block)

        return AccessResult(
            access=access,
            hit=False,
            block=block,
            set_index=set_index,
            tag=tag,
            line_index=line_index,
            evicted_tag=evicted_tag,
            writeback=writeback,
        )

    def run(self, accesses: Iterable[Access | int]) -> SimulationStats:
        """Execute a trace and return the cumulative statistics."""

        for access in accesses:
            self.access(access)
        return self.stats

    def _update_shadow_cache(self, block: int) -> None:
        """Update the fully associative LRU cache used for 3C classification."""

        self._seen_blocks.add(block)
        if block in self._shadow_lru:
            self._shadow_lru.move_to_end(block)
        else:
            self._shadow_lru[block] = None
            if len(self._shadow_lru) > self.config.number_of_lines:
                self._shadow_lru.popitem(last=False)
