"""Read-only profiling of the raw loans, used by notebooks/01_data_audit.ipynb.

Everything here reads the Parquet cache written by ingest.py and changes nothing.
The analysis queries live in sql/analysis/*.sql and are run with run_sql_file().
The raw table is all text, so column types are inferred from the values.
"""

from pathlib import Path

import duckdb
import pandas as pd

from credit_risk.config import (
    ANALYSIS_SQL_DIR,
    DEFAULT_STATUSES,
    GOOD_STATUSES,
    LOANS_RAW_PARQUET,
    MODEL_APPLICATION_TYPE,
    MODEL_TERM_MONTHS,
    TEST_END,
    TEST_START,
    TRAIN_START,
    VALIDATION_START,
)

RAW_LOANS_VIEW = "raw_loans"
LOANS_AUDIT_VIEW = "loans_audit"

# The raw file has non-loan footer lines ("Total amount funded in policy code 1: ...").
# A real loan has a numeric id; clean.py must apply the same rule.
LOAN_ROWS = "try_cast(id AS BIGINT) IS NOT NULL"

_PERCENT_PATTERN = r"\s*\d+(\.\d+)?%\s*"  # e.g. ' 13.56%'
_MON_YEAR_PATTERN = r"[A-Z][a-z]{2}-\d{4}"  # e.g. 'Dec-2015'


def open_raw_loans(parquet_path: Path = LOANS_RAW_PARQUET) -> duckdb.DuckDBPyConnection:
    """Return an in-memory connection with a `raw_loans` view over the raw Parquet file."""
    if not parquet_path.is_file():
        raise FileNotFoundError(f"{parquet_path} not found. Run `python run_pipeline.py --from ingest`.")
    con = duckdb.connect(":memory:")
    source = parquet_path.as_posix().replace("'", "''")
    con.execute(f"CREATE VIEW {RAW_LOANS_VIEW} AS SELECT * FROM read_parquet('{source}')")
    return con


def row_counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Count all rows, real loans, and non-loan rows (footer lines) in the raw table."""
    total, loans = con.execute(
        f"SELECT count(*), count(*) FILTER (WHERE {LOAN_ROWS}) FROM {RAW_LOANS_VIEW}"
    ).fetchone()
    return {"total_rows": total, "loan_rows": loans, "non_loan_rows": total - loans}


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _infer_type(n_present: int, n_numeric: int, n_percent: int, n_mon_year: int) -> str:
    """Name the one format that every non-missing value of a column follows."""
    if n_present == 0:
        return "empty"
    for label, n_matching in (("numeric", n_numeric), ("percent_text", n_percent), ("mon_year_text", n_mon_year)):
        if n_matching == n_present:
            return label
    return "mixed" if n_numeric else "text"


def profile_columns(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """One row per column: inferred type, missing count and %, distinct values (loan rows only)."""
    n_loans = row_counts(con)["loan_rows"]
    columns = [row[0] for row in con.execute(f"DESCRIBE {RAW_LOANS_VIEW}").fetchall()]
    rows = []
    for name in columns:
        col = _quote(name)
        n_present, n_numeric, n_percent, n_mon_year, n_distinct = con.execute(
            f"""
            SELECT count({col}),
                   count(try_cast({col} AS DOUBLE)),
                   count(*) FILTER (WHERE regexp_full_match({col}, '{_PERCENT_PATTERN}')),
                   count(*) FILTER (WHERE regexp_full_match({col}, '{_MON_YEAR_PATTERN}')),
                   count(DISTINCT {col})
            FROM {RAW_LOANS_VIEW} WHERE {LOAN_ROWS}
            """
        ).fetchone()
        rows.append(
            {
                "column": name,
                "inferred_type": _infer_type(n_present, n_numeric, n_percent, n_mon_year),
                "n_missing": n_loans - n_present,
                "pct_missing": round(100 * (n_loans - n_present) / n_loans, 2),
                "n_distinct": n_distinct,
            }
        )
    return pd.DataFrame(rows)


def _sql_list(values: frozenset[str]) -> str:
    """Render a set of strings as a DuckDB list literal, e.g. ['Charged Off', 'Default']."""
    return "[" + ", ".join("'" + v.replace("'", "''") + "'" for v in sorted(values)) + "]"


def create_audit_view(con: duckdb.DuckDBPyConnection) -> None:
    """Create `loans_audit`: the raw loan rows plus typed helper columns for the SQL queries.

    Adds issue_date, issue_year, issue_month, term_months, outcome ('default', 'fully_paid' or
    'unresolved', using the status lists in config.py) and is_default (1, 0, or NULL while
    unresolved). Every raw column is kept as text. Safe to call more than once.
    """
    con.execute(
        f"""
        CREATE OR REPLACE VIEW {LOANS_AUDIT_VIEW} AS
        SELECT *,
               year(issue_date) AS issue_year,
               month(issue_date) AS issue_month,
               CASE outcome WHEN 'default' THEN 1 WHEN 'fully_paid' THEN 0 END AS is_default
        FROM (
            SELECT *,
                   try_strptime(issue_d, '%b-%Y')::DATE AS issue_date,
                   try_cast(regexp_extract(term, '(\\d+)', 1) AS INTEGER) AS term_months,
                   CASE
                       WHEN list_contains({_sql_list(DEFAULT_STATUSES)}, loan_status) THEN 'default'
                       WHEN list_contains({_sql_list(GOOD_STATUSES)}, loan_status) THEN 'fully_paid'
                       ELSE 'unresolved'
                   END AS outcome
            FROM {RAW_LOANS_VIEW} WHERE {LOAN_ROWS}
        )
        """
    )


# Values a query may reference as $name. Only the ones a query uses are passed to DuckDB,
# which rejects parameters that do not appear in the SQL.
_SQL_PARAMETERS = {
    "model_term_months": MODEL_TERM_MONTHS,
    "model_application_type": MODEL_APPLICATION_TYPE,
    "train_start": TRAIN_START,
    "validation_start": VALIDATION_START,
    "test_start": TEST_START,
    "test_end": TEST_END,
}


def run_sql_file(
    con: duckdb.DuckDBPyConnection, name: str, sql_dir: Path = ANALYSIS_SQL_DIR
) -> pd.DataFrame:
    """Run sql/analysis/<name>.sql against the `loans_audit` view and return the result.

    `name` is the file name without `.sql`, e.g. "04_resolved_share_by_term_and_year".
    """
    path = sql_dir / f"{name.removesuffix('.sql')}.sql"
    if not path.is_file():
        raise FileNotFoundError(f"No SQL file {path}")
    create_audit_view(con)
    sql = path.read_text(encoding="utf-8")
    parameters = {k: v for k, v in _SQL_PARAMETERS.items() if f"${k}" in sql}
    return con.execute(sql, parameters or None).df()
