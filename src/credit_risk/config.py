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
DOCS_DIR = PROJECT_ROOT / "docs"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# ---- Raw inputs (never edited) ---------------------------------------------
# Lending Club accepted loans, 2007 to 2018 Q4 (Kaggle). The extracted CSV sits
# inside a folder of the same name, as produced by unzipping the download.
LOANS_CSV = RAW_DIR / "accepted_2007_to_2018q4.csv" / "accepted_2007_to_2018Q4.csv"
LOANS_CSV_GZ = RAW_DIR / "accepted_2007_to_2018Q4.csv.gz"
LC_DATA_DICTIONARY = RAW_DIR / "LCDataDictionary.xlsx"

# FRED unemployment series (data/external/)
FRED_STATE_UNEMPLOYMENT_CSV = EXTERNAL_DIR / "monthly.csv"  # 50 states + DC, series like CAUR
FRED_NATIONAL_UNEMPLOYMENT_CSV = EXTERNAL_DIR / "UNRATE.csv"  # US national rate

# ---- Processed outputs -----------------------------------------------------
DUCKDB_PATH = PROCESSED_DIR / "credit_risk.duckdb"
LOANS_RAW_PARQUET = INTERIM_DIR / "loans_raw.parquet"  # raw CSV as Parquet, fast to reload
LOANS_CLEAN_PARQUET = INTERIM_DIR / "loans_clean.parquet"
LOANS_PROCESSED_PARQUET = PROCESSED_DIR / "loans_processed.parquet"  # model-ready table
MODEL_PATH = MODELS_DIR / "xgb_default_model.json"

# ---- Reproducibility -------------------------------------------------------
RANDOM_SEED = 42

# ---- Out-of-time split (by issue year) -------------------------------------
# Train on older loans, tune on the next year, score the final test year once.
# Adjust after the data audit shows how many resolved loans each year has:
# 2017-2018 loans are often still unresolved and biased towards early defaults.
TRAIN_END_YEAR = 2014  # train: issue year <= 2014
VALIDATION_YEAR = 2015
TEST_YEAR = 2016

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
