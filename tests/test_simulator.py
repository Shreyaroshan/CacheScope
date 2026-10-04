import pytest

from cachescope import Access, CacheConfig, CacheSimulator


def test_same_block_produces_a_hit() -> None:
    simulator = CacheSimulator(CacheConfig(cache_size=64, block_size=16))

    first = simulator.access(0)
    second = simulator.access(15)

    assert not first.hit
    assert second.hit
    assert simulator.stats.hits == 1
    assert simulator.stats.misses == 1


def test_direct_mapped_conflict_evicts_existing_line() -> None:
    simulator = CacheSimulator(CacheConfig(cache_size=64, block_size=16))

    simulator.access(0)
    result = simulator.access(64)

    assert not result.hit
    assert result.set_index == 0
    assert result.evicted_tag == 0
    assert simulator.stats.evictions == 1


def test_lru_evicts_least_recently_used_line() -> None:
    simulator = CacheSimulator(
        CacheConfig(cache_size=32, block_size=16, associativity=2, policy="lru")
    )

    simulator.run([0, 16, 0])
    eviction = simulator.access(32)

    assert eviction.evicted_tag == 1
    assert simulator.access(0).hit
    assert not simulator.access(16).hit


def test_fifo_ignores_hits_when_selecting_victim() -> None:
    simulator = CacheSimulator(
        CacheConfig(cache_size=32, block_size=16, associativity=2, policy="fifo")
    )

    simulator.run([0, 16, 0])
    eviction = simulator.access(32)

    assert eviction.evicted_tag == 0
    assert simulator.access(16).hit
    assert not simulator.access(0).hit


def test_dirty_eviction_counts_a_writeback() -> None:
    simulator = CacheSimulator(CacheConfig(cache_size=16, block_size=16))

    simulator.access(Access(0, "W"))
    eviction = simulator.access(16)

    assert eviction.writeback
    assert simulator.stats.writebacks == 1


def test_metrics_and_amat() -> None:
    config = CacheConfig(
        cache_size=64, block_size=16, hit_time=2.0, miss_penalty=50.0
    )
    simulator = CacheSimulator(config)
    stats = simulator.run([0, 4, 16, 20])

    assert stats.hits == 2
    assert stats.misses == 2
    assert stats.hit_rate == pytest.approx(0.5)
    assert stats.miss_rate == pytest.approx(0.5)
    assert stats.amat(config.hit_time, config.miss_penalty) == pytest.approx(27.0)


def test_reset_clears_lines_and_statistics() -> None:
    simulator = CacheSimulator(CacheConfig(cache_size=64, block_size=16))
    simulator.run([0, 0])

    simulator.reset()

    assert simulator.stats.accesses == 0
    assert not simulator.access(0).hit


def test_compulsory_conflict_and_capacity_misses() -> None:
    conflict = CacheSimulator(CacheConfig(cache_size=32, block_size=16))
    conflict.run([0, 32, 0])

    assert conflict.stats.compulsory_misses == 2
    assert conflict.stats.conflict_misses == 1
    assert conflict.stats.capacity_misses == 0

    capacity = CacheSimulator(
        CacheConfig(cache_size=32, block_size=16, associativity=2)
    )
    capacity.run([0, 16, 32, 0])

    assert capacity.stats.compulsory_misses == 3
    assert capacity.stats.conflict_misses == 0
    assert capacity.stats.capacity_misses == 1
    assert (
        capacity.stats.compulsory_misses
        + capacity.stats.conflict_misses
        + capacity.stats.capacity_misses
        == capacity.stats.misses
    )
