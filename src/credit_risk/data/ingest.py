"""Load raw Lending Club and macro files into DuckDB.

Raw files in data/raw/ are never modified: this module only reads them.
"""

from pathlib import Path

import duckdb

from credit_risk.config import DUCKDB_PATH, RAW_DIR


def get_connection(db_path: Path = DUCKDB_PATH) -> duckdb.DuckDBPyConnection:
    """Open (or create) the project DuckDB database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def load_raw_loans(con: duckdb.DuckDBPyConnection, raw_dir: Path = RAW_DIR) -> None:
    """Load the raw Lending Club CSV(s) into a `raw_loans` table."""
    # TODO: point at the downloaded file(s), e.g. raw_dir / "accepted_2007_to_2018Q4.csv"
    raise NotImplementedError("load_raw_loans: implement once the raw data is downloaded")


def load_macro(con: duckdb.DuckDBPyConnection) -> None:
    """Load FRED / Bank of England series from data/external/ into DuckDB."""
    raise NotImplementedError("load_macro: implement once macro data is downloaded")


def run() -> None:
    """Pipeline entry point."""
    with get_connection() as con:
        load_raw_loans(con)
        load_macro(con)
