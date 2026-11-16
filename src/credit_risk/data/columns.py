"""Read docs/column_classification.csv and answer "which columns play this role?".

The CSV is the single record of what happens to each raw column. Cleaning, feature building
and the data dictionary all read it through here, so they cannot drift apart.
"""

import csv
from pathlib import Path

from credit_risk.config import COLUMN_CLASSIFICATION_CSV, FEATURE_SET_CORE


def read_classification(path: Path = COLUMN_CLASSIFICATION_CSV) -> list[dict[str, str]]:
    """Read the classification as a list of row dicts, in the CSV's (raw column) order."""
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def columns_with_roles(rows: list[dict[str, str]], *roles: str) -> list[str]:
    """Names of the columns whose role is one of `roles`, in classification order."""
    return [r["column"] for r in rows if r["role"] in roles]


def feature_columns(
    rows: list[dict[str, str]], feature_sets: tuple[str, ...] = (FEATURE_SET_CORE,)
) -> list[str]:
    """Model features in the given feature sets: core only for the headline model."""
    return [r["column"] for r in rows if r["role"] == "feature" and r["feature_set"] in feature_sets]
