import json

from cachescope.cli import main


def test_cli_text_report(capsys) -> None:
    result = main(
        [
            "--cache-size",
            "64",
            "--block-size",
            "16",
            "--count",
            "4",
            "--step",
            "16",
        ]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "accesses: 4" in output
    assert "hit rate: 0.00%" in output


def test_cli_json_report(capsys) -> None:
    result = main(["--count", "2", "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["config"]["policy"] == "lru"
    assert payload["stats"]["accesses"] == 2


def test_cli_batch_comparison_and_csv(tmp_path, capsys) -> None:
    destination = tmp_path / "comparison.csv"

    result = main(
        [
            "--count",
            "8",
            "--compare-cache-sizes",
            "64,128",
            "--compare-associativities",
            "1,2",
            "--compare-policies",
            "lru,fifo",
            "--csv",
            str(destination),
        ]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "hit rate" in output
    assert "CSV written" in output
    assert destination.read_text(encoding="utf-8").startswith("cache_size,")
