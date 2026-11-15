"""Data quality checks. Each check raises AssertionError with a clear message."""

import pandas as pd


def check_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = sorted(set(required) - set(df.columns))
    assert not missing, f"Missing required columns: {missing}"


def check_unique(df: pd.DataFrame, key: str) -> None:
    dupes = int(df[key].duplicated().sum())
    assert dupes == 0, f"{dupes} duplicate values in key column '{key}'"


def check_range(df: pd.DataFrame, col: str, low: float, high: float) -> None:
    bad = int((~df[col].dropna().between(low, high)).sum())
    assert bad == 0, f"{bad} values in '{col}' outside [{low}, {high}]"


def run() -> None:
    """Pipeline entry point: validate the interim tables."""
    raise NotImplementedError("validate.run: add checks for the cleaned loans table")
