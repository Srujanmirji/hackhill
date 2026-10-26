from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")
PARQUET = Path(__file__).resolve().parents[1] / "data" / "processed" / "gold_futures.parquet"


@pytest.fixture(autouse=True)
def clear_app_cache():
    st.cache_data.clear()
    yield
    st.cache_data.clear()


@pytest.mark.parametrize("failure", [FileNotFoundError("missing"), ValueError("invalid dataset"), TypeError("invalid column type")])
def test_dataset_failure_shows_recovery_without_traceback(monkeypatch, failure):
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(pd, "read_parquet", fail)
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert "Rebuild it" in at.error[0].value
    assert "scripts/build_dataset.py --raw data/raw" in at.code[0].value


def test_missing_pair_keeps_picker_and_other_pairs_available(monkeypatch):
    from aulens.data.loader import tidy
    from aulens.data.sample import make_sample
    df = tidy(make_sample(start="2025-04-01", end="2025-08-31"))
    df = df[df["symbol"].isin(["GOLDTEN", "GOLDPETAL"])].assign(source="SYNTHETIC")
    monkeypatch.setattr(pd, "read_parquet", lambda *args, **kwargs: df.copy())
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert "No overlapping contract dates" in at.info[0].value
    assert any("Latest dataset date" in c.value for c in at.caption)
    at.button_group(key="pair").set_value(2).run()
    assert not at.exception
    assert any("Selected pair's latest overlapping date" in c.value for c in at.caption)
    assert at.get("download_button")
    assert any("No final untouched holdout is claimed" in c.value for c in at.caption)
    assert any("Validation evidence and model limits" == e.label for e in at.expander)
    assert any(d.label == "Monthly validation evidence (.csv)" for d in at.get("download_button"))


@pytest.mark.skipif(not PARQUET.exists(), reason="real dataset not built")
def test_real_dashboard_loads_and_shows_freshness():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception and not at.error
    assert any("Latest dataset date" in c.value for c in at.caption)
    assert any("not a live quote feed" in c.value for c in at.caption)
    assert at.get("download_button")
    assert any("No final untouched holdout is claimed" in c.value for c in at.caption)
    assert any("Validation evidence and model limits" == e.label for e in at.expander)
    assert any(d.label == "Monthly validation evidence (.csv)" for d in at.get("download_button"))


@pytest.mark.skipif(not PARQUET.exists(), reason="real dataset not built")
def test_silver_only_data_shows_gold_chart_recovery(monkeypatch):
    df = pd.read_parquet(PARQUET)
    df = df[df["symbol"].isin(["SILVERM", "SILVERMIC"])]
    monkeypatch.setattr(pd, "read_parquet", lambda *args, **kwargs: df.copy())
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.button_group(key="pair").set_value(4).run()
    assert not at.exception
    assert any("Load GOLDTEN history" in i.value for i in at.info)
    assert not any("nan" in c.value.lower() for c in at.caption)


def test_short_history_disables_evidence_download(monkeypatch):
    from aulens.data.loader import tidy
    from aulens.data.sample import make_sample
    df = tidy(make_sample(start="2025-04-01", end="2025-05-30")).assign(source="SYNTHETIC")
    monkeypatch.setattr(pd, "read_parquet", lambda *args, **kwargs: df.copy())
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert any("No test months yet" in i.value for i in at.info)
    evidence = next(d for d in at.get("download_button") if d.label == "Monthly validation evidence (.csv)")
    assert evidence.disabled
