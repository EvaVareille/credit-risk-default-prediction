"""Data quality checks on the cleaned and processed loan tables.

Each `check_*` function raises AssertionError with a clear message. `validate_processed` runs
all of them and reports every failure at once, and `run()` is the pipeline step.
"""

import logging

import pandas as pd

from credit_risk.config import (
    LOANS_OUTCOMES_PARQUET,
    LOANS_PROCESSED_PARQUET,
    TARGET,
    TEST_END,
    TEST_START,
    TRAIN_START,
    VALIDATION_START,
    WINSOR_CAPS_JSON,
)
from credit_risk.data.clean import ID_COLUMN, load_caps
from credit_risk.data.columns import columns_with_roles, read_classification
from credit_risk.features.build_features import (
    DERIVED_CORE_FEATURES,
    DERIVED_LC_ASSESSMENT_FEATURES,
    REPLACED_COLUMNS,
    SPLIT_COLUMN,
    TEST,
    TRAIN,
    VALIDATION,
)

logger = logging.getLogger(__name__)

# Rows and default rate per split, from the audit (sql/analysis/07_modelling_population.sql)
# and docs/cleaning_log.md. If the population rules change, update these on purpose.
EXPECTED_SPLITS = {
    TRAIN: (262_992, 0.1319),
    VALIDATION: (120_790, 0.1512),
    TEST: (161_997, 0.1470),
}
DEFAULT_RATE_TOLERANCE = 0.0005

# Fields that must never be missing.
REQUIRED_NOT_NULL = [
    ID_COLUMN, "issue_d", TARGET, SPLIT_COLUMN, "addr_state",
    "loan_amnt", "annual_inc", "fico_range_low", "fico_range_high", "state_unemployment_rate",
]

# Plausible ranges (low, high), inclusive. Missing values are allowed here; the check above
# decides which fields may not be missing.
VALUE_RANGES = {
    "loan_amnt": (500, 40_000),
    "annual_inc": (0, 10_000_000),
    "dti": (0, 100),
    "fico_range_low": (300, 850),
    "fico_range_high": (300, 850),
    "fico_mid": (300, 850),
    "int_rate": (0, 40),
    "emp_length": (0, 10),
    "revol_util": (0, 1000),
    "credit_history_years": (0, 100),
    "loan_to_income": (0, 5),
    "issue_month": (1, 12),
    "state_unemployment_rate": (0, 30),
}


def check_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = sorted(set(required) - set(df.columns))
    assert not missing, f"Missing required columns: {missing}"


def check_no_unexpected_columns(df: pd.DataFrame, allowed: set[str]) -> None:
    """Fail if the table has a column nobody approved: a leakage guard."""
    extra = sorted(set(df.columns) - allowed)
    assert not extra, f"Unexpected columns (leakage?): {extra}"


def check_unique(df: pd.DataFrame, key: str) -> None:
    dupes = int(df[key].duplicated().sum())
    assert dupes == 0, f"{dupes} duplicate values in key column '{key}'"


def check_no_nulls(df: pd.DataFrame, columns: list[str]) -> None:
    counts = df[columns].isna().sum()
    bad = {c: int(n) for c, n in counts.items() if n}
    assert not bad, f"Missing values in required columns: {bad}"


def check_range(df: pd.DataFrame, col: str, low: float, high: float) -> None:
    bad = int((~df[col].dropna().between(low, high)).sum())
    assert bad == 0, f"{bad} values in '{col}' outside [{low}, {high}]"


def check_values_in(df: pd.DataFrame, col: str, allowed: set) -> None:
    bad = sorted(set(df[col].dropna().unique()) - allowed)
    assert not bad, f"Unexpected values in '{col}': {bad}"


def check_split_matches_dates(df: pd.DataFrame) -> None:
    """Each loan's split must agree with its issue date, and all loans must be in the period."""
    issued = df["issue_d"]
    in_period = issued.between(pd.Timestamp(TRAIN_START), pd.Timestamp(TEST_END), inclusive="left")
    assert in_period.all(), f"{int((~in_period).sum())} loans issued outside the modelling period"
    expected = pd.Series(TRAIN, index=df.index)
    expected[issued >= pd.Timestamp(VALIDATION_START)] = VALIDATION
    expected[issued >= pd.Timestamp(TEST_START)] = TEST
    wrong = int((df[SPLIT_COLUMN] != expected).sum())
    assert wrong == 0, f"{wrong} loans have a split that disagrees with their issue date"


def check_split_sizes(df: pd.DataFrame, expected: dict[str, tuple[int, float]] = EXPECTED_SPLITS) -> None:
    """Row counts and default rates per split must match the audit."""
    problems = []
    for split, (n_expected, rate_expected) in expected.items():
        rows = df[df[SPLIT_COLUMN] == split]
        rate = float(rows[TARGET].mean()) if len(rows) else float("nan")
        if len(rows) != n_expected:
            problems.append(f"{split}: {len(rows):,} loans, expected {n_expected:,}")
        if not abs(rate - rate_expected) <= DEFAULT_RATE_TOLERANCE:
            problems.append(f"{split}: default rate {rate:.4f}, expected {rate_expected:.4f}")
    assert not problems, "Split sizes differ from the audit: " + "; ".join(problems)


def check_outcomes_align(features: pd.DataFrame, outcomes: pd.DataFrame) -> None:
    """The outcome table must hold exactly the same loans, in the same order."""
    assert len(features) == len(outcomes), (
        f"{len(features):,} feature rows but {len(outcomes):,} outcome rows"
    )
    assert (features[ID_COLUMN].to_numpy() == outcomes[ID_COLUMN].to_numpy()).all(), (
        "Feature and outcome tables have different ids or a different order"
    )


def check_within_caps(df: pd.DataFrame, caps: dict[str, float]) -> None:
    over = {c: int((df[c] > cap).sum()) for c, cap in caps.items() if c in df and (df[c] > cap).any()}
    assert not over, f"Values above their outlier cap: {over}"


def validate_processed(
    features: pd.DataFrame,
    outcomes: pd.DataFrame,
    classification: list[dict[str, str]],
    caps: dict[str, float],
) -> None:
    """Run every check on the processed tables; raise one AssertionError listing all failures."""
    feature_columns = set(columns_with_roles(classification, "identifier", "split_key", "target", "feature"))
    allowed = (
        feature_columns - set(REPLACED_COLUMNS)
        | {TARGET, SPLIT_COLUMN, *DERIVED_CORE_FEATURES, *DERIVED_LC_ASSESSMENT_FEATURES}
    )
    ranges = {c: r for c, r in VALUE_RANGES.items() if c in features}

    checks = [
        lambda: check_required_columns(features, REQUIRED_NOT_NULL),
        lambda: check_no_unexpected_columns(features, allowed),
        lambda: check_unique(features, ID_COLUMN),
        lambda: check_no_nulls(features, [c for c in REQUIRED_NOT_NULL if c in features]),
        lambda: check_values_in(features, TARGET, {0, 1}),
        lambda: check_values_in(features, SPLIT_COLUMN, {TRAIN, VALIDATION, TEST}),
        *[(lambda c=c, lo=lo, hi=hi: check_range(features, c, lo, hi)) for c, (lo, hi) in ranges.items()],
        lambda: check_split_matches_dates(features),
        lambda: check_split_sizes(features, EXPECTED_SPLITS),
        lambda: check_outcomes_align(features, outcomes),
        lambda: check_unique(outcomes, ID_COLUMN),
        lambda: check_within_caps(features, caps),
    ]
    failures = []
    for check in checks:
        try:
            check()
        except (AssertionError, KeyError) as exc:
            failures.append(str(exc))
    assert not failures, "Validation failed:\n  - " + "\n  - ".join(failures)


def run() -> None:
    """Pipeline entry point: validate the processed tables."""
    validate_processed(
        pd.read_parquet(LOANS_PROCESSED_PARQUET),
        pd.read_parquet(LOANS_OUTCOMES_PARQUET),
        read_classification(),
        load_caps(WINSOR_CAPS_JSON),
    )
    logger.info("All data checks passed")
