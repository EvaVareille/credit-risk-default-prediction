"""Load the raw Lending Club loans into DuckDB and cache them as Parquet.

Raw files in data/raw/ are never modified: this module only reads them. Every
column is loaded as text and no rows are dropped, so the raw table mirrors the
file exactly (including its two non-loan footer lines). Typing and row removal
happen in clean.py and are recorded in docs/cleaning_log.md.
"""

import logging
from pathlib import Path

import duckdb

from credit_risk.config import DUCKDB_PATH, LOANS_CSV, LOANS_RAW_PARQUET

logger = logging.getLogger(__name__)

RAW_LOANS_TABLE = "raw_loans"


def get_connection(db_path: Path = DUCKDB_PATH) -> duckdb.DuckDBPyConnection:
    """Open (or create) the project DuckDB database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def load_raw_loans(con: duckdb.DuckDBPyConnection, csv_path: Path = LOANS_CSV) -> int:
    """Load the raw loans CSV into the `raw_loans` table and return its row count.

    Replaces any existing table, so re-running gives the same result.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Raw loans file not found: {csv_path}. See README 'Data sources'.")
    con.execute(
        f"CREATE OR REPLACE TABLE {RAW_LOANS_TABLE} AS SELECT * FROM read_csv(?, all_varchar = true)",
        [str(csv_path)],
    )
    return con.execute(f"SELECT count(*) FROM {RAW_LOANS_TABLE}").fetchone()[0]


def export_raw_loans_parquet(
    con: duckdb.DuckDBPyConnection, parquet_path: Path = LOANS_RAW_PARQUET
) -> None:
    """Write the `raw_loans` table to Parquet, which reloads much faster than the CSV."""
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    target = parquet_path.as_posix().replace("'", "''")  # COPY cannot take a bound parameter
    con.execute(f"COPY {RAW_LOANS_TABLE} TO '{target}' (FORMAT parquet, COMPRESSION zstd)")


def run() -> None:
    """Pipeline entry point: raw CSV -> DuckDB table -> Parquet."""
    with get_connection() as con:
        n_rows = load_raw_loans(con)
        logger.info("Loaded %s rows into %s", f"{n_rows:,}", RAW_LOANS_TABLE)
        export_raw_loans_parquet(con)
        logger.info("Wrote %s", LOANS_RAW_PARQUET)
