"""Read-only profiling of the raw loans, used by notebooks/01_data_audit.ipynb.

Everything here reads the Parquet cache written by ingest.py and changes nothing.
The raw table is all text, so column types are inferred from the values.
"""

from pathlib import Path

import duckdb
import pandas as pd

from credit_risk.config import DEFAULT_STATUSES, GOOD_STATUSES, LOANS_RAW_PARQUET

RAW_LOANS_VIEW = "raw_loans"

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


def _outcome(status: str | None) -> str:
    if status in DEFAULT_STATUSES:
        return "default"
    if status in GOOD_STATUSES:
        return "fully_paid"
    return "unresolved"


def loan_status_counts(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Value counts of loan_status with the outcome each status maps to in the target."""
    counts = con.execute(
        f"""
        SELECT loan_status AS status, count(*) AS n_loans
        FROM {RAW_LOANS_VIEW} WHERE {LOAN_ROWS}
        GROUP BY loan_status ORDER BY n_loans DESC
        """
    ).df()
    counts["pct"] = (100 * counts["n_loans"] / counts["n_loans"].sum()).round(2)
    counts["outcome"] = counts["status"].map(_outcome)
    return counts


def loans_per_issue_year(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Loans, resolved loans and default rate by issue year, to choose the out-of-time split."""
    by_year = con.execute(
        f"""
        SELECT year(strptime(issue_d, '%b-%Y')) AS issue_year,
               count(*) AS n_loans,
               count(*) FILTER (WHERE list_contains(?, loan_status)) AS n_default,
               count(*) FILTER (WHERE list_contains(?, loan_status)) AS n_fully_paid
        FROM {RAW_LOANS_VIEW} WHERE {LOAN_ROWS}
        GROUP BY issue_year ORDER BY issue_year
        """,
        [sorted(DEFAULT_STATUSES), sorted(GOOD_STATUSES)],
    ).df()
    by_year["n_resolved"] = by_year["n_default"] + by_year["n_fully_paid"]
    by_year["default_rate"] = (by_year["n_default"] / by_year["n_resolved"]).round(4)
    return by_year.drop(columns="n_fully_paid")
