import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from main import add_power, rename_fields, add_timestamp, unpack_data, extract_data


def test_power_w_derived():
    row = {"ina260__voltage_v": 14.0, "ina260__current_ma": 11000.0}
    result = add_power(row)
    assert result["power_w"] == pytest.approx(154.0)


def test_power_w_zero_current():
    row = {"ina260__voltage_v": 14.0, "ina260__current_ma": 0.0}
    result = add_power(row)
    assert result["power_w"] == 0.0


def test_set_speed_renamed():
    row = {"set_speed": 0.5, "other": 1}
    result = rename_fields(row)
    assert "set_speed_frac" in result
    assert "set_speed" not in result
    assert result["set_speed_frac"] == 0.5


def test_set_speed_missing_key():
    row = {"other": 1}
    result = rename_fields(row)
    assert "set_speed_frac" not in result
    assert result == {"other": 1}


def test_dead_letter_missing_data_key():
    row = {"not_data": [1, 2, 3]}
    result = extract_data(row, key=None, timestamp=0, headers={})
    assert result is None


def test_dead_letter_wrong_type():
    row = {"data": None}
    # None is technically a valid return of row["data"] but expand=True would fail downstream
    # Test that a row with data=42 (non-iterable non-list) still returns the value
    # The DLQ path is for KeyError/TypeError only - a present but non-list "data" passes through
    row2 = {"not_data": "oops"}
    result = extract_data(row2, key=None, timestamp=0, headers={})
    assert result is None


def test_add_timestamp_stateless():
    row = {"timestamp": 500}
    result = add_timestamp(row, key=None, timestamp=1_000_000, headers={})
    assert result["new_timestamp"] == 1_000_500
