"""Project-wide paths, constants and the random seed.

Import from here rather than hard-coding paths, so notebooks, scripts,
the app and tests all agree on where things live.
"""

from pathlib import Path

# ---- Paths -----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXTERNAL_DIR = DATA_DIR / "external"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

SQL_DIR = PROJECT_ROOT / "sql"
MODELS_DIR = PROJECT_ROOT / "models"
APP_DATA_DIR = PROJECT_ROOT / "app" / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

DUCKDB_PATH = PROCESSED_DIR / "credit_risk.duckdb"
MODEL_PATH = MODELS_DIR / "xgb_default_model.json"

# ---- Reproducibility -------------------------------------------------------
RANDOM_SEED = 42
TEST_SIZE = 0.2

# ---- Target definition -----------------------------------------------------
TARGET = "is_default"

# Lending Club loan_status values treated as a default (1) or fully repaid (0).
# Loans still running ("Current", "In Grace Period", ...) are excluded.
DEFAULT_STATUSES = frozenset({
    "Charged Off",
    "Default",
    "Does not meet the credit policy. Status:Charged Off",
})
GOOD_STATUSES = frozenset({
    "Fully Paid",
    "Does not meet the credit policy. Status:Fully Paid",
})
