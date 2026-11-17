import pandas as pd
import pytest

from credit_risk.data import validate
from credit_risk.data.validate import (
    check_no_nulls,
    check_no_unexpected_columns,
    check_outcomes_align,
    check_range,
    check_required_columns,
    check_split_matches_dates,
    check_split_sizes,
    check_unique,
    check_values_in,
    check_within_caps,
)


def _table():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "issue_d": pd.to_datetime(["2013-05-01", "2015-02-01", "2015-09-01"]),
        "split": ["train", "validation", "test"],
        "is_default": [0, 1, 0],
    })


def test_check_required_columns():
    check_required_columns(_table(), ["id", "split"])
    with pytest.raises(AssertionError, match="nope"):
        check_required_columns(_table(), ["id", "nope"])


def test_check_no_unexpected_columns_flags_a_leaky_column():
    df = _table().assign(total_pymnt=1.0)
    check_no_unexpected_columns(_table(), set(_table().columns))
    with pytest.raises(AssertionError, match="total_pymnt"):
        check_no_unexpected_columns(df, set(_table().columns))


def test_check_unique():
    check_unique(_table(), "id")
    with pytest.raises(AssertionError, match="duplicate"):
        check_unique(pd.concat([_table(), _table()]), "id")


def test_check_no_nulls_names_the_column_and_count():
    df = _table()
    df.loc[0, "is_default"] = None
    with pytest.raises(AssertionError, match="is_default.*1"):
        check_no_nulls(df, ["id", "is_default"])


def test_check_range_ignores_missing_values():
    check_range(pd.DataFrame({"x": [1.0, None, 5.0]}), "x", 0, 10)
    with pytest.raises(AssertionError, match="outside"):
        check_range(pd.DataFrame({"x": [1.0, 11.0]}), "x", 0, 10)


def test_check_values_in():
    check_values_in(_table(), "is_default", {0, 1})
    with pytest.raises(AssertionError, match="2"):
        check_values_in(_table().assign(is_default=[0, 1, 2]), "is_default", {0, 1})


def test_check_split_matches_dates():
    check_split_matches_dates(_table())
    wrong = _table().assign(split=["train", "train", "test"])
    with pytest.raises(AssertionError, match="disagrees"):
        check_split_matches_dates(wrong)
    late = _table().assign(issue_d=pd.to_datetime(["2013-05-01", "2015-02-01", "2016-01-01"]))
    with pytest.raises(AssertionError, match="outside the modelling period"):
        check_split_matches_dates(late)


def test_check_split_sizes_compares_counts_and_default_rates():
    expected = {"train": (1, 0.0), "validation": (1, 1.0), "test": (1, 0.0)}
    check_split_sizes(_table(), expected)
    with pytest.raises(AssertionError, match="expected 2"):
        check_split_sizes(_table(), {**expected, "train": (2, 0.0)})
    with pytest.raises(AssertionError, match="default rate"):
        check_split_sizes(_table(), {**expected, "test": (1, 0.5)})


def test_check_outcomes_align_needs_same_ids_in_same_order():
    outcomes = pd.DataFrame({"id": [1, 2, 3], "total_pymnt": [1.0, 2.0, 3.0]})
    check_outcomes_align(_table(), outcomes)
    with pytest.raises(AssertionError, match="different ids"):
        check_outcomes_align(_table(), outcomes.iloc[::-1].reset_index(drop=True))
    with pytest.raises(AssertionError, match="rows"):
        check_outcomes_align(_table(), outcomes.iloc[:2])


def test_check_within_caps():
    df = pd.DataFrame({"a": [1.0, 100.0]})
    check_within_caps(df, {"a": 100.0, "not_in_table": 5.0})
    with pytest.raises(AssertionError, match="a"):
        check_within_caps(df, {"a": 50.0})


def test_validate_processed_reports_every_failure_at_once(monkeypatch):
    monkeypatch.setattr(validate, "EXPECTED_SPLITS", {"train": (1, 0.0)})
    features = _table().assign(extra=1)  # not allowed
    features.loc[0, "is_default"] = 5  # not 0 or 1
    classification = [
        {"column": c, "role": role}
        for c, role in [("id", "identifier"), ("issue_d", "split_key"), ("is_default", "target")]
    ]
    outcomes = pd.DataFrame({"id": [1, 2, 3]})
    with pytest.raises(AssertionError) as error:
        validate.validate_processed(features, outcomes, classification, {})
    message = str(error.value)
    assert "extra" in message and "is_default" in message
