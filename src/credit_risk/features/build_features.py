"""Turn cleaned loans into a model-ready table."""

import numpy as np
import pandas as pd

from credit_risk.config import DEFAULT_STATUSES, GOOD_STATUSES, TARGET


def make_target(df: pd.DataFrame, status_col: str = "loan_status") -> pd.DataFrame:
    """Add the binary target and drop loans whose outcome is not yet known."""
    known = df[status_col].isin(DEFAULT_STATUSES | GOOD_STATUSES)
    out = df.loc[known].copy()
    out[TARGET] = out[status_col].isin(DEFAULT_STATUSES).astype("int8")
    return out


def add_ratio_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add affordability ratios. Division by zero income gives NaN, not inf."""
    out = df.copy()
    income = out["annual_inc"].replace(0, np.nan)
    out["loan_to_income"] = out["loan_amnt"] / income
    out["instalment_to_monthly_income"] = out["installment"] / (income / 12)
    return out


def run() -> None:
    """Pipeline entry point: interim -> processed model table."""
    raise NotImplementedError("build_features.run: wire up once cleaning is done")
