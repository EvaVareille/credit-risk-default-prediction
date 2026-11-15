"""Cleaning functions.

Every decision made here should be recorded in docs/cleaning_log.md.
"""

import re

import pandas as pd


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


def clean_loans(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning steps to the raw loans table."""
    out = standardise_column_names(df)
    for col in ("int_rate", "revol_util"):
        if col in out:
            out[col] = parse_percent(out[col])
    if "emp_length" in out:
        out["emp_length"] = parse_emp_length(out["emp_length"])
    # TODO: drop leakage columns (post-origination fields such as total_pymnt, recoveries)
    return out


def run() -> None:
    """Pipeline entry point: read raw loans, clean, write to data/interim/."""
    raise NotImplementedError("clean.run: wire up raw -> interim once ingest is done")
