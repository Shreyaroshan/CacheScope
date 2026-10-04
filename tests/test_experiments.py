import csv
from io import StringIO

from cachescope.experiments import results_to_csv, run_experiments


def test_batch_runs_same_trace_for_every_valid_configuration() -> None:
    results = run_experiments(
        [0, 16, 0, 32],
        cache_sizes=[32, 64],
        block_sizes=[16],
        associativities=[1, 2],
        policies=["lru", "fifo"],
    )

    assert len(results) == 8
    assert all(result.accesses == 4 for result in results)
    assert {result.policy for result in results} == {"lru", "fifo"}


def test_batch_skips_invalid_geometry() -> None:
    results = run_experiments(
        [0],
        cache_sizes=[32],
        block_sizes=[16],
        associativities=[1, 3],
    )

    assert results
    assert all(result.associativity == 1 for result in results)


def test_csv_contains_metrics_and_miss_classes() -> None:
    results = run_experiments(
        [0, 32, 0],
        cache_sizes=[32],
        block_sizes=[16],
        associativities=[1],
        policies=["lru"],
    )

    rows = list(csv.DictReader(StringIO(results_to_csv(results))))
    assert rows[0]["conflict_misses"] == "1"
    assert "hit_rate" in rows[0]
    assert "amat" in rows[0]
