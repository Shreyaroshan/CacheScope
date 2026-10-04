from app import _synthetic_trace


def test_app_trace_generation_is_deterministic() -> None:
    first = _synthetic_trace("Random", 5, 0, 1, 64, 100, 7)
    second = _synthetic_trace("Random", 5, 0, 1, 64, 100, 7)

    assert first == second


def test_streamlit_app_loads_and_runs_both_workflows() -> None:
    import pytest

    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file("app.py", default_timeout=20).run()
    assert not app.exception
    assert [item.value for item in app.title] == ["CacheScope"]

    app.number_input[0].set_value(32)
    app.button[0].click().run()
    assert not app.exception
    assert len(app.metric) == 4

    app.button[1].click().run()
    assert not app.exception
    assert len(app.dataframe) == 1
    assert len(app.get("download_button")) == 1
