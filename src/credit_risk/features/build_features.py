"""Turn cleaned loans into a model-ready table.

`run()` reads data/interim/loans_clean.parquet and writes data/processed/loans_processed.parquet:
`id`, `issue_d`, the out-of-time `split`, the target `is_default` and the model features.

Derived features use only what the lender knows at application. `issue_d` stays for the split
(and the FRED join) but is not a feature: only the issue month is derived from it, because
trees cannot extrapolate to years they have not seen.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from credit_risk.config import (
    FRED_STATE_UNEMPLOYMENT_CSV,
    LOANS_CLEAN_PARQUET,
    LOANS_PROCESSED_PARQUET,
    TEST_END,
    TEST_START,
    VALIDATION_START,
)

logger = logging.getLogger(__name__)

SPLIT_COLUMN = "split"
TRAIN, VALIDATION, TEST = "train", "validation", "test"

# Derived columns by feature set. The headline model uses `core`; the ablation adds `lc_assessment`.
UNEMPLOYMENT_COLUMN = "state_unemployment_rate"
DERIVED_CORE_FEATURES = [
    "loan_to_income", "credit_history_years", "fico_mid", "issue_month", UNEMPLOYMENT_COLUMN,
]
DERIVED_LC_ASSESSMENT_FEATURES = ["instalment_to_monthly_income"]
# Raw columns that a derived feature replaces. They leave the model table.
REPLACED_COLUMNS = ["earliest_cr_line"]


def add_ratio_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the affordability ratios of the headline model. Zero income gives NaN, not inf."""
    out = df.copy()
    income = out["annual_inc"].replace(0, np.nan)
    out["loan_to_income"] = out["loan_amnt"] / income
    return out


def add_credit_history_years(df: pd.DataFrame) -> pd.DataFrame:
    """Add years from the earliest credit line to the issue date. Negative values become NaN."""
    out = df.copy()
    years = (out["issue_d"] - out["earliest_cr_line"]).dt.days / 365.25
    out["credit_history_years"] = years.where(years >= 0)
    return out


def add_fico_mid(df: pd.DataFrame) -> pd.DataFrame:
    """Add the midpoint of the FICO range, the single score the range stands for."""
    out = df.copy()
    out["fico_mid"] = (out["fico_range_low"] + out["fico_range_high"]) / 2
    return out


def add_issue_month(df: pd.DataFrame) -> pd.DataFrame:
    """Add the calendar month (1 to 12) of the issue date, for seasonality. Never the year."""
    out = df.copy()
    out["issue_month"] = out["issue_d"].dt.month.astype("float64")
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


def read_state_unemployment(path: Path = FRED_STATE_UNEMPLOYMENT_CSV) -> pd.DataFrame:
    """Read the FRED state file (one `XXUR` column per state) as long rows: state, month, rate.

    `month` is the first day of the month the rate describes, so it lines up with `issue_d`.
    """
    wide = pd.read_csv(path, parse_dates=["observation_date"])
    long = wide.melt(id_vars="observation_date", var_name="series", value_name=UNEMPLOYMENT_COLUMN)
    long["addr_state"] = long["series"].str.removesuffix("UR")
    long = long.rename(columns={"observation_date": "month"})
    return long[["addr_state", "month", UNEMPLOYMENT_COLUMN]].dropna()


def add_state_unemployment(df: pd.DataFrame, unemployment: pd.DataFrame) -> pd.DataFrame:
    """Add the state unemployment rate for the month BEFORE the loan was issued.

    The current month's rate is not published at application time, so it would leak the future.
    Loans with no matching state and month get NaN. Row order and count are unchanged, and an
    error is raised if the join would duplicate loans.
    """
    previous_month = (df["issue_d"] - pd.offsets.MonthBegin(1)).rename("month")
    keys = pd.concat([df["addr_state"], previous_month], axis=1)
    merged = keys.merge(unemployment, on=["addr_state", "month"], how="left")
    if len(merged) != len(df):
        raise ValueError("The unemployment table has duplicate state and month rows")
    out = df.copy()
    out[UNEMPLOYMENT_COLUMN] = merged[UNEMPLOYMENT_COLUMN].to_numpy()
    return out


def assign_split(df: pd.DataFrame) -> pd.DataFrame:
    """Add the out-of-time split from the issue date, using the dates in config.py.

    Train is everything before the validation start, validation runs up to the test start, and
    test up to the end of the test period. Loans issued later raise an error: they should
    not be in the table.
    """
    out = df.copy()
    issued = out["issue_d"]
    if (issued >= pd.Timestamp(TEST_END)).any():
        raise ValueError(f"Loans issued on or after {TEST_END} are outside the modelling period")
    out[SPLIT_COLUMN] = np.select(
        [issued >= pd.Timestamp(TEST_START), issued >= pd.Timestamp(VALIDATION_START)],
        [TEST, VALIDATION],
        default=TRAIN,
    )
    return out


def build_features(df: pd.DataFrame, unemployment: pd.DataFrame) -> pd.DataFrame:
    """Cleaned loans -> model-ready table: derived features, split label, replaced columns dropped."""
    out = add_ratio_features(df)
    out = add_state_unemployment(out, unemployment)
    out = add_credit_history_years(out)
    out = add_fico_mid(out)
    out = add_issue_month(out)
    out = add_lc_assessment_features(out)
    out = assign_split(out)
    return out.drop(columns=REPLACED_COLUMNS)


def run() -> None:
    """Pipeline entry point: interim -> processed model table."""
    loans = pd.read_parquet(LOANS_CLEAN_PARQUET)
    table = build_features(loans, read_state_unemployment())
    LOANS_PROCESSED_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(LOANS_PROCESSED_PARQUET, index=False)
    missing = int(table[UNEMPLOYMENT_COLUMN].isna().sum())
    if missing:
        logger.warning("%s loans have no state unemployment rate", f"{missing:,}")
    counts = table[SPLIT_COLUMN].value_counts().to_dict()
    logger.info("Wrote %s (%s rows, %s columns); splits %s",
                LOANS_PROCESSED_PARQUET, f"{len(table):,}", table.shape[1], counts)
