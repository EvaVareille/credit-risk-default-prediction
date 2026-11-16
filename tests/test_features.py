import numpy as np
import pandas as pd

from credit_risk.features.build_features import (
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
