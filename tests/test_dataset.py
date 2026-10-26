import pandas as pd
import pytest

from aulens.data.loader import load_processed


@pytest.fixture
def frame():
    return pd.DataFrame({"date": pd.to_datetime(["2025-04-01"]), "symbol": ["GOLDTEN"],
                         "expiry": pd.to_datetime(["2025-04-30"]), "close": [90000.0],
                         "volume": [100], "oi": [50], "source": ["MCX"]})


def test_load_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_processed(tmp_path / "absent.parquet")


@pytest.mark.parametrize("case", ["empty", "column", "date", "price", "volume", "null", "duplicate", "source"])
def test_load_rejects_invalid_data(tmp_path, frame, case):
    if case == "empty":
        frame = frame.iloc[:0]
    elif case == "column":
        frame = frame.drop(columns="oi")
    elif case == "date":
        frame["date"] = "invalid"
    elif case == "price":
        frame["close"] = float("inf")
    elif case == "volume":
        frame["volume"] = -1
    elif case == "null":
        frame["expiry"] = pd.NaT
    elif case == "duplicate":
        frame = pd.concat([frame, frame])
    elif case == "source":
        frame["source"] = "UNKNOWN"
    path = tmp_path / "data.parquet"
    frame.to_parquet(path)
    with pytest.raises(ValueError):
        load_processed(path)


def test_valid_data_is_preserved(tmp_path, frame):
    path = tmp_path / "data.parquet"
    frame.to_parquet(path)
    pd.testing.assert_frame_equal(load_processed(path), frame)


@pytest.mark.parametrize("column", ["date", "expiry"])
def test_timezone_dates_get_a_recoverable_validation_error(tmp_path, frame, column):
    frame[column] = frame[column].dt.tz_localize("UTC")
    path = tmp_path / "data.parquet"
    frame.to_parquet(path)
    with pytest.raises(ValueError, match="without a timezone"):
        load_processed(path)
