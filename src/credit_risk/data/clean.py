"""Cleaning: pick the modelling loans from the raw table, fix their types, set the outcomes aside.

Every decision made here should be recorded in docs/cleaning_log.md. Which columns are kept,
dropped or set aside is decided in docs/column_classification.csv, not in this file.

`run()` reads data/interim/loans_raw.parquet and writes two tables:
- data/interim/loans_clean.parquet: one row per modelling loan with `id`, `issue_d`, the target
  `is_default` and every feature (both feature sets, so the ablation can use them).
- data/processed/loans_outcomes.parquet: `id` plus the post-issue columns that are only for
  evaluation (the profit curve). They are never joined to the features.
"""

import logging
import re
from pathlib import Path

import duckdb
import pandas as pd

from credit_risk.config import (
    COLUMN_CLASSIFICATION_CSV,
    DEFAULT_STATUSES,
    GOOD_STATUSES,
    LOANS_CLEAN_PARQUET,
    LOANS_OUTCOMES_PARQUET,
    LOANS_RAW_PARQUET,
    MODEL_APPLICATION_TYPE,
    MODEL_TERM_MONTHS,
    TARGET,
    TEST_END,
    TRAIN_START,
)
from credit_risk.data.audit import LOANS_AUDIT_VIEW, create_audit_view, open_raw_loans
from credit_risk.data.columns import columns_with_roles, read_classification

logger = logging.getLogger(__name__)

ID_COLUMN = "id"
STATUS_COLUMN = "loan_status"
DATE_COLUMNS = frozenset({"issue_d", "earliest_cr_line", "last_pymnt_d"})  # text like 'Dec-2015'
TEXT_COLUMNS = frozenset(
    {STATUS_COLUMN, "purpose", "home_ownership", "verification_status", "addr_state", "grade", "sub_grade"}
)
PERCENT_COLUMNS = frozenset({"int_rate", "revol_util"})
# Any other selected column is a number. emp_length is text ('10+ years') converted to years.

_MONTHS = {
    name: f"{number:02d}"
    for number, name in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1
    )
}


def standardise_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case column names and replace non-alphanumerics with underscores."""
    out = df.copy()
    out.columns = [re.sub(r"[^0-9a-z]+", "_", c.strip().lower()).strip("_") for c in out.columns]
    return out


def parse_percent(s: pd.Series) -> pd.Series:
    """Convert strings like ' 13.56%' to floats (13.56). Blanks become NaN."""
    return pd.to_numeric(s.astype("string").str.strip().str.rstrip("%"), errors="coerce")


def parse_emp_length(s: pd.Series) -> pd.Series:
    """Convert Lending Club emp_length ('< 1 year', '10+ years') to years as a number."""
    text = s.astype("string").str.strip()
    years = pd.to_numeric(text.str.extract(r"(\d+)", expand=False), errors="coerce")
    under_one_year = text.str.startswith("<").fillna(False).astype(bool)
    return years.mask(under_one_year, 0).astype("Float64")


def parse_month_year(s: pd.Series) -> pd.Series:
    """Convert strings like 'Dec-2015' to the first day of that month. Anything else is NaT.

    Month names are matched here rather than by pandas, so the result does not depend on the
    machine's language settings.
    """
    parts = s.astype("string").str.strip().str.extract(r"^([A-Za-z]{3})-(\d{4})$")
    month = parts[0].map(_MONTHS).astype("string")
    return pd.to_datetime(parts[1] + "-" + month + "-01", format="%Y-%m-%d", errors="coerce")


def make_target(df: pd.DataFrame, status_col: str = STATUS_COLUMN) -> pd.DataFrame:
    """Add the binary target and drop loans whose outcome is not yet known."""
    known = df[status_col].isin(DEFAULT_STATUSES | GOOD_STATUSES)
    out = df.loc[known].copy()
    out[TARGET] = out[status_col].isin(DEFAULT_STATUSES).astype("int8")
    return out


def clean_loans(df: pd.DataFrame) -> pd.DataFrame:
    """Fix the types of a table of raw text columns.

    Raises ValueError if any value would be lost in the conversion (a value that is present as
    text but cannot be read as a number or date), so a type problem cannot pass unnoticed.
    """
    out = standardise_column_names(df)
    lost = {}
    for column in out.columns:
        raw = out[column]
        if column in TEXT_COLUMNS:
            out[column] = raw.astype("string").str.strip()
            continue
        if column in DATE_COLUMNS:
            typed = parse_month_year(raw)
        elif column == "emp_length":
            typed = parse_emp_length(raw)
        elif column in PERCENT_COLUMNS:
            typed = parse_percent(raw)
        else:
            typed = pd.to_numeric(raw, errors="coerce")
        n_lost = int((raw.notna() & typed.isna()).sum())
        if n_lost:
            lost[column] = n_lost
        out[column] = typed
    if lost:
        raise ValueError(f"Values could not be converted and would be lost: {lost}")
    for column in out.columns:  # plain numpy types, so every library reads the table the same way
        if column == ID_COLUMN:
            out[column] = out[column].astype("int64")
        elif column not in TEXT_COLUMNS and column not in DATE_COLUMNS:
            out[column] = out[column].astype("float64")
    return out


def select_modelling_loans(con: duckdb.DuckDBPyConnection, columns: list[str]) -> pd.DataFrame:
    """Read `columns` (as raw text) for the loans the model is built on, ordered by id.

    A loan is in the modelling population if it has a final outcome, the modelling term and
    application type, and was issued from the training start up to (not including) the end of
    the test period. The rules come from config.py and reuse the audit's `loans_audit` view,
    so the audit and the cleaned table cannot disagree about which loans these are.
    """
    create_audit_view(con)
    available = {row[0] for row in con.execute(f"DESCRIBE {LOANS_AUDIT_VIEW}").fetchall()}
    missing = [c for c in columns if c not in available]
    if missing:
        raise ValueError(f"Columns in the classification but not in the raw data: {missing}")
    select_list = ", ".join('"' + c.replace('"', '""') + '"' for c in columns)
    return con.execute(
        f"""
        SELECT {select_list} FROM {LOANS_AUDIT_VIEW}
        WHERE outcome <> 'unresolved'
          AND term_months = ?
          AND trim(application_type) = ?
          AND issue_date >= ? AND issue_date < ?
        ORDER BY CAST(id AS BIGINT)
        """,
        [MODEL_TERM_MONTHS, MODEL_APPLICATION_TYPE, TRAIN_START, TEST_END],
    ).df()


def split_outcomes(df: pd.DataFrame, outcome_columns: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate the evaluation-only columns: returns (features table, outcomes table by id)."""
    outcomes = df[[ID_COLUMN, *outcome_columns]].copy()
    features = df.drop(columns=outcome_columns)
    return features, outcomes


def run(
    raw_parquet: Path = LOANS_RAW_PARQUET,
    clean_path: Path = LOANS_CLEAN_PARQUET,
    outcomes_path: Path = LOANS_OUTCOMES_PARQUET,
    classification_path: Path = COLUMN_CLASSIFICATION_CSV,
) -> None:
    """Pipeline entry point: raw loans -> clean features table and outcomes table."""
    rows = read_classification(classification_path)
    keep = columns_with_roles(rows, "identifier", "split_key", "target", "feature")
    outcome_columns = columns_with_roles(rows, "eval_only")

    con = open_raw_loans(raw_parquet)
    try:
        raw = select_modelling_loans(con, keep + outcome_columns)
    finally:
        con.close()
    logger.info("Selected %s modelling loans, %s columns", f"{len(raw):,}", raw.shape[1])

    loans = make_target(clean_loans(raw)).drop(columns=STATUS_COLUMN)
    features, outcomes = split_outcomes(loans, outcome_columns)

    for path, table in ((clean_path, features), (outcomes_path, outcomes)):
        path.parent.mkdir(parents=True, exist_ok=True)
        table.to_parquet(path, index=False)
        logger.info("Wrote %s (%s rows, %s columns)", path, f"{len(table):,}", table.shape[1])
