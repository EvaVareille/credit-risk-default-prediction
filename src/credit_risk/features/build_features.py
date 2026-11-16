"""Turn cleaned loans into a model-ready table."""

import numpy as np
import pandas as pd


def add_ratio_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the affordability ratios of the headline model. Zero income gives NaN, not inf."""
    out = df.copy()
    income = out["annual_inc"].replace(0, np.nan)
    out["loan_to_income"] = out["loan_amnt"] / income
    return out


def add_lc_assessment_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add features for the ablation run only (feature set `lc_assessment`).

    `installment` is calculated from the loan amount, term and interest rate, so with a fixed
    term it reveals the rate. Ratios built from it therefore stay out of the headline model.
    """
    out = df.copy()
    income = out["annual_inc"].replace(0, np.nan)
    out["instalment_to_monthly_income"] = out["installment"] / (income / 12)
    return out


def run() -> None:
    """Pipeline entry point: interim -> processed model table."""
    raise NotImplementedError("build_features.run: wire up once cleaning is done")
