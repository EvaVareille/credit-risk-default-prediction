import numpy as np
import pandas as pd

from credit_risk.config import TARGET
from credit_risk.features.build_features import add_ratio_features, make_target


def test_make_target_drops_unknown_outcomes():
    df = pd.DataFrame({"loan_status": ["Fully Paid", "Charged Off", "Current", "Default"]})
    out = make_target(df)
    assert out["loan_status"].tolist() == ["Fully Paid", "Charged Off", "Default"]
    assert out[TARGET].tolist() == [0, 1, 1]


def test_add_ratio_features_handles_zero_income():
    df = pd.DataFrame({"loan_amnt": [10_000, 5_000], "installment": [300, 150], "annual_inc": [50_000, 0]})
    out = add_ratio_features(df)
    assert out["loan_to_income"].iloc[0] == 0.2
    assert np.isnan(out["loan_to_income"].iloc[1])
    assert out["instalment_to_monthly_income"].iloc[0] == 300 / (50_000 / 12)
