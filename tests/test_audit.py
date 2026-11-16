import csv

import duckdb
import pytest

from credit_risk.config import ANALYSIS_SQL_DIR
from credit_risk.data import audit
from credit_risk.data.ingest import export_raw_loans_parquet, load_raw_loans

CSV_TEXT = (
    "id,loan_amnt,int_rate,issue_d,loan_status,note\n"
    "1,1000.0, 13.56%,Dec-2015,Fully Paid,a\n"
    "2,2000.0,7.9%,Jan-2015,Charged Off,\n"
    "3,3000.0,9.1%,Jan-2016,Current,\n"
    "Total amount funded in policy code 1: 99,,,,,\n"
)


def _open_audit_connection(tmp_path, csv_text):
    """Write `csv_text` as the raw file, ingest it, and open it the way the audit does."""
    csv_path = tmp_path / "loans.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    parquet_path = tmp_path / "loans.parquet"
    with duckdb.connect(":memory:") as source:
        load_raw_loans(source, csv_path)
        export_raw_loans_parquet(source, parquet_path)
    return audit.open_raw_loans(parquet_path)


@pytest.fixture
def con(tmp_path):
    connection = _open_audit_connection(tmp_path, CSV_TEXT)
    yield connection
    connection.close()


# Columns the SQL files read, and nine loans chosen so that every query has a known answer:
#   id  issue    term  status      type   grade   what it exercises
#   1   2013-01  36    Fully Paid  Indiv  A       train
#   2   2013-06  36    Charged Off Indiv  B       train
#   3   2015-01  36    Fully Paid  Indiv  B       validation
#   4   2015-01  60    Current     Indiv  C       unresolved, 60-month
#   5   2015-08  36    Charged Off Indiv  C       test
#   6   2016-01  36    Charged Off Indiv  A       after the test period
#   7   2012-12  36    Fully Paid  Indiv  A       before the training start
#   8   2014-01  36    Late        Indiv  A       unresolved
#   9   2015-09  36    Fully Paid  Joint  C       joint application
# plus a footer line that is not a loan.
SQL_COLUMNS = [
    "id", "issue_d", "term", "loan_status", "application_type", "grade", "tot_cur_bal",
    "mort_acc", "mths_since_last_major_derog", "mths_since_recent_bc_dlq",
    "mths_since_recent_revol_delinq", "open_acc_6m", "il_util", "inq_last_12m",
    "mths_since_last_delinq",
]
SQL_LOANS = [
    ("1", "Jan-2013", " 36 months", "Fully Paid", "Individual", "A", "5000"),
    ("2", "Jun-2013", " 36 months", "Charged Off", "Individual", "B", "6000"),
    ("3", "Jan-2015", " 36 months", "Fully Paid", "Individual", "B", "7000"),
    ("4", "Jan-2015", " 60 months", "Current", "Individual", "C", "8000"),
    ("5", "Aug-2015", " 36 months", "Charged Off", "Individual", "C", "9000"),
    ("6", "Jan-2016", " 36 months", "Charged Off", "Individual", "A", "1000"),
    ("7", "Dec-2012", " 36 months", "Fully Paid", "Individual", "A", ""),
    ("8", "Jan-2014", " 36 months", "Late (31-120 days)", "Individual", "A", "2000"),
    ("9", "Sep-2015", " 36 months", "Fully Paid", "Joint App", "C", "3000"),
]


def _sql_csv_text():
    from io import StringIO

    out = StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(SQL_COLUMNS)
    for loan in SQL_LOANS:
        writer.writerow(list(loan) + [""] * (len(SQL_COLUMNS) - len(loan)))
    writer.writerow(["Total amount funded in policy code 1: 99"] + [""] * (len(SQL_COLUMNS) - 1))
    return out.getvalue()


@pytest.fixture
def sql_con(tmp_path):
    connection = _open_audit_connection(tmp_path, _sql_csv_text())
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


def test_audit_view_adds_typed_columns_and_drops_footer(sql_con):
    audit.create_audit_view(sql_con)
    view = sql_con.execute(
        "SELECT id, issue_year, issue_month, term_months, outcome, is_default "
        "FROM loans_audit ORDER BY CAST(id AS INTEGER)"
    ).df()

    assert len(view) == 9  # the footer line is gone
    assert view.loc[0, ["issue_year", "issue_month", "term_months"]].tolist() == [2013, 1, 36]
    assert view.loc[3, "term_months"] == 60
    assert view["outcome"].tolist() == [
        "fully_paid", "default", "fully_paid", "unresolved", "default",
        "default", "fully_paid", "unresolved", "fully_paid",
    ]
    assert view.loc[1, "is_default"] == 1 and view.loc[0, "is_default"] == 0
    # is_default is empty exactly for the two unresolved loans (ids 4 and 8)
    assert view["is_default"].isna().tolist() == [False, False, False, True, False, False, False, True, False]


def test_audit_view_can_be_created_twice(sql_con):
    audit.create_audit_view(sql_con)
    audit.create_audit_view(sql_con)


def test_run_sql_file_missing_file_raises(sql_con):
    with pytest.raises(FileNotFoundError):
        audit.run_sql_file(sql_con, "99_does_not_exist")


def test_loans_per_year(sql_con):
    by_year = audit.run_sql_file(sql_con, "01_loans_per_year").set_index("issue_year")

    assert by_year.loc[2013, "n_loans"] == 2
    assert by_year.loc[2015, "n_loans"] == 4
    assert by_year.loc[2015, "n_resolved"] == 3  # the Current loan is not resolved
    assert by_year.loc[2015, "default_rate"] == pytest.approx(0.3333)  # 1 of 3 resolved


def test_status_breakdown_maps_outcomes(sql_con):
    status = audit.run_sql_file(sql_con, "02_status_breakdown").set_index("status")

    assert status.loc["Fully Paid", ["n_loans", "outcome"]].tolist() == [4, "fully_paid"]
    assert status.loc["Charged Off", "outcome"] == "default"
    assert status.loc["Late (31-120 days)", "outcome"] == "unresolved"
    assert status["n_loans"].sum() == 9
    assert status["pct"].sum() == pytest.approx(100, abs=0.1)


def test_default_rate_by_grade_ignores_unresolved_loans(sql_con):
    by_grade = audit.run_sql_file(sql_con, "03_default_rate_by_grade").set_index("grade")

    assert by_grade.loc["A", "n_loans"] == 3  # the Late grade-A loan is excluded
    assert by_grade.loc["A", "default_rate"] == pytest.approx(0.3333)
    assert by_grade.loc["B", "default_rate"] == 0.5
    assert by_grade.loc["C", "n_loans"] == 2  # the Current grade-C loan is excluded


def test_resolved_share_by_term_and_year(sql_con):
    share = audit.run_sql_file(sql_con, "04_resolved_share_by_term_and_year")
    share = share.set_index(["issue_year", "term_months"])

    assert share.loc[(2015, 60), "pct_resolved"] == 0.0
    assert share.loc[(2015, 36), ["n_loans", "n_resolved"]].tolist() == [3, 3]
    assert share.loc[(2015, 36), "default_rate"] == pytest.approx(0.3333)


def test_missingness_by_year(sql_con):
    missing = audit.run_sql_file(sql_con, "05_missingness_by_year").set_index("issue_year")

    assert missing.loc[2012, "tot_cur_bal"] == 100.0  # loan 7 has it empty
    assert missing.loc[2013, "tot_cur_bal"] == 0.0
    assert missing.loc[2013, "open_acc_6m"] == 100.0  # never filled in the fixture


def test_application_type_by_year(sql_con):
    by_year = audit.run_sql_file(sql_con, "06_application_type_by_year").set_index("issue_year")

    assert by_year.loc[2015, ["n_loans", "n_joint", "pct_joint"]].tolist() == [4, 1, 25.0]
    assert by_year.loc[2013, "n_joint"] == 0


def test_modelling_population_funnel_and_splits(sql_con):
    funnel = audit.run_sql_file(sql_con, "07_modelling_population").set_index("step_no")

    assert funnel["n_loans"].tolist() == [9, 7, 7, 6, 5, 2, 1, 1, 1]
    # train, validation, test and the excluded 2016 loan add up to the loans from the start date
    assert funnel.loc[6:9, "n_loans"].sum() == funnel.loc[5, "n_loans"]
    assert funnel.loc[6, "default_rate"] == 0.5  # loans 1 and 2


@pytest.mark.parametrize("path", sorted(ANALYSIS_SQL_DIR.glob("*.sql")), ids=lambda p: p.stem)
def test_every_analysis_sql_file_runs(sql_con, path):
    result = audit.run_sql_file(sql_con, path.stem)
    assert len(result) > 0
