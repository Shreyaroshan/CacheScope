import pytest

from cachescope import CacheConfig, CacheSimulator


def test_cache_geometry() -> None:
    config = CacheConfig(cache_size=1024, block_size=64, associativity=4)

    assert config.number_of_lines == 16
    assert config.number_of_sets == 4


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cache_size": 0, "block_size": 16},
        {"cache_size": 100, "block_size": 16},
        {"cache_size": 64, "block_size": 16, "associativity": 3},
        {"cache_size": 64, "block_size": 16, "policy": "random"},
    ],
)
def test_invalid_configs_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        CacheConfig(**kwargs)  # type: ignore[arg-type]


def test_address_mapping() -> None:
    simulator = CacheSimulator(
        CacheConfig(cache_size=64, block_size=16, associativity=1)
    )

    assert simulator.map_address(0) == (0, 0, 0)
    assert simulator.map_address(15) == (0, 0, 0)
    assert simulator.map_address(16) == (1, 1, 0)
    assert simulator.map_address(64) == (4, 0, 1)


def test_negative_address_is_rejected() -> None:
    simulator = CacheSimulator(CacheConfig(cache_size=64, block_size=16))

    with pytest.raises(ValueError):
        simulator.map_address(-1)
