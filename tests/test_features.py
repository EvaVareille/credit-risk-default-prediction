import numpy as np
import pandas as pd
import pytest

from credit_risk.features.build_features import (
    DERIVED_CORE_FEATURES,
    DERIVED_LC_ASSESSMENT_FEATURES,
    add_credit_history_years,
    add_fico_mid,
    add_issue_month,
    assign_split,
    build_features,
    add_lc_assessment_features,
    add_ratio_features,
)


def test_add_ratio_features_handles_zero_income():
    df = pd.DataFrame({"loan_amnt": [10_000, 5_000], "installment": [300, 150], "annual_inc": [50_000, 0]})
    out = add_ratio_features(df)
    assert out["loan_to_income"].iloc[0] == 0.2
    assert np.isnan(out["loan_to_income"].iloc[1])


def test_headline_ratio_features_do_not_use_the_instalment():
    df = pd.DataFrame({"loan_amnt": [10_000], "installment": [300], "annual_inc": [50_000]})
    assert "instalment_to_monthly_income" not in add_ratio_features(df).columns


def test_add_lc_assessment_features_adds_the_instalment_ratio():
    df = pd.DataFrame({"installment": [300, 150], "annual_inc": [50_000, 0]})
    out = add_lc_assessment_features(df)
    assert out["instalment_to_monthly_income"].iloc[0] == 300 / (50_000 / 12)
    assert np.isnan(out["instalment_to_monthly_income"].iloc[1])


def test_credit_history_years_and_negative_gap():
    df = pd.DataFrame({
        "issue_d": pd.to_datetime(["2014-01-01", "2014-01-01"]),
        "earliest_cr_line": pd.to_datetime(["2004-01-01", "2014-06-01"]),
    })
    out = add_credit_history_years(df)
    assert abs(out["credit_history_years"].iloc[0] - 10.0) < 0.01
    assert np.isnan(out["credit_history_years"].iloc[1])


def test_fico_mid_is_the_midpoint():
    out = add_fico_mid(pd.DataFrame({"fico_range_low": [660.0], "fico_range_high": [664.0]}))
    assert out["fico_mid"].iloc[0] == 662.0


def test_issue_month_has_no_year_information():
    out = add_issue_month(pd.DataFrame({"issue_d": pd.to_datetime(["2013-03-01", "2015-03-01"])}))
    assert out["issue_month"].tolist() == [3.0, 3.0]


def test_assign_split_follows_config_dates_and_rejects_later_loans():
    df = pd.DataFrame({"issue_d": pd.to_datetime(
        ["2013-01-01", "2014-12-01", "2015-01-01", "2015-06-01", "2015-07-01", "2015-12-01"])})
    assert assign_split(df)["split"].tolist() == [
        "train", "train", "validation", "validation", "test", "test"]
    with pytest.raises(ValueError):
        assign_split(pd.DataFrame({"issue_d": pd.to_datetime(["2016-01-01"])}))


def test_build_features_drops_replaced_columns_and_adds_derived_ones():
    df = pd.DataFrame({
        "id": [1], "is_default": [0], "loan_amnt": [10_000.0], "installment": [300.0],
        "annual_inc": [50_000.0], "fico_range_low": [700.0], "fico_range_high": [704.0],
        "issue_d": pd.to_datetime(["2014-05-01"]), "earliest_cr_line": pd.to_datetime(["2004-05-01"]),
    })
    out = build_features(df)
    assert "earliest_cr_line" not in out.columns
    for column in [*DERIVED_CORE_FEATURES, *DERIVED_LC_ASSESSMENT_FEATURES, "split"]:
        assert column in out.columns
