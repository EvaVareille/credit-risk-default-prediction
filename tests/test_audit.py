import duckdb
import pytest

from credit_risk.data import audit
from credit_risk.data.ingest import export_raw_loans_parquet, load_raw_loans

CSV_TEXT = (
    "id,loan_amnt,int_rate,issue_d,loan_status,note\n"
    "1,1000.0, 13.56%,Dec-2015,Fully Paid,a\n"
    "2,2000.0,7.9%,Jan-2015,Charged Off,\n"
    "3,3000.0,9.1%,Jan-2016,Current,\n"
    "Total amount funded in policy code 1: 99,,,,,\n"
)


@pytest.fixture
def con(tmp_path):
    csv_path = tmp_path / "loans.csv"
    csv_path.write_text(CSV_TEXT, encoding="utf-8")
    parquet_path = tmp_path / "loans.parquet"
    with duckdb.connect(":memory:") as source:
        load_raw_loans(source, csv_path)
        export_raw_loans_parquet(source, parquet_path)
    connection = audit.open_raw_loans(parquet_path)
    yield connection
    connection.close()


def test_open_raw_loans_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        audit.open_raw_loans(tmp_path / "missing.parquet")


def test_row_counts_separates_footer_lines(con):
    assert audit.row_counts(con) == {"total_rows": 4, "loan_rows": 3, "non_loan_rows": 1}


def test_profile_columns_infers_types_and_missing(con):
    profile = audit.profile_columns(con).set_index("column")

    assert profile.loc["loan_amnt", "inferred_type"] == "numeric"
    assert profile.loc["int_rate", "inferred_type"] == "percent_text"
    assert profile.loc["issue_d", "inferred_type"] == "mon_year_text"
    assert profile.loc["loan_status", "inferred_type"] == "text"
    assert profile.loc["note", "n_missing"] == 2  # footer row excluded from the base
    assert profile.loc["note", "pct_missing"] == pytest.approx(66.67)


def test_loan_status_counts_maps_outcomes(con):
    counts = audit.loan_status_counts(con).set_index("status")

    assert counts.loc["Fully Paid", "outcome"] == "fully_paid"
    assert counts.loc["Charged Off", "outcome"] == "default"
    assert counts.loc["Current", "outcome"] == "unresolved"
    assert counts["n_loans"].sum() == 3


def test_loans_per_issue_year_default_rate_uses_resolved_loans_only(con):
    by_year = audit.loans_per_issue_year(con).set_index("issue_year")

    assert by_year.loc[2015, "n_resolved"] == 2
    assert by_year.loc[2015, "default_rate"] == 0.5
    assert by_year.loc[2016, "n_resolved"] == 0  # only a Current loan
