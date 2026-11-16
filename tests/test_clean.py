import duckdb
import pandas as pd
import pytest

from credit_risk.config import TARGET
from credit_risk.data import audit, clean
from credit_risk.data.clean import (
    clean_loans,
    make_target,
    parse_emp_length,
    parse_month_year,
    parse_percent,
    split_outcomes,
    standardise_column_names,
)
from credit_risk.data.ingest import export_raw_loans_parquet, load_raw_loans


def test_standardise_column_names():
    df = pd.DataFrame(columns=["Loan Amnt", " int_rate ", "Emp-Length"])
    assert list(standardise_column_names(df).columns) == ["loan_amnt", "int_rate", "emp_length"]


def test_parse_percent():
    out = parse_percent(pd.Series([" 13.56%", "7%", None, ""]))
    assert out.iloc[0] == 13.56
    assert out.iloc[1] == 7
    assert out.iloc[2:].isna().all()


def test_parse_emp_length():
    out = parse_emp_length(pd.Series(["< 1 year", "1 year", "5 years", "10+ years", None]))
    assert out.iloc[:4].tolist() == [0, 1, 5, 10]
    assert pd.isna(out.iloc[4])


def test_parse_month_year_reads_dates_and_turns_the_rest_into_nat():
    out = parse_month_year(pd.Series(["Dec-2015", " Jan-2013 ", None, "", "Foo-2015", "Dec-15"]))
    assert out.iloc[:2].tolist() == [pd.Timestamp("2015-12-01"), pd.Timestamp("2013-01-01")]
    assert out.iloc[2:].isna().all()  # a missing date must not stop the rest being read


def test_make_target_drops_unknown_outcomes():
    df = pd.DataFrame({"loan_status": ["Fully Paid", "Charged Off", "Current", "Default"]})
    out = make_target(df)
    assert out["loan_status"].tolist() == ["Fully Paid", "Charged Off", "Default"]
    assert out[TARGET].tolist() == [0, 1, 1]


def test_clean_loans_converts_every_column_to_its_type():
    raw = pd.DataFrame({
        "id": ["10", "20"],
        "issue_d": ["Dec-2015", "Jan-2013"],
        "int_rate": ["13.56", None],
        "emp_length": ["10+ years", "< 1 year"],
        "annual_inc": ["50000.0", None],
        "grade": [" B ", "A"],
        "last_pymnt_d": [None, "Mar-2016"],
    })
    out = clean_loans(raw)
    assert str(out["id"].dtype) == "int64"
    assert out["issue_d"].tolist() == [pd.Timestamp("2015-12-01"), pd.Timestamp("2013-01-01")]
    assert str(out["int_rate"].dtype) == "float64" and out["int_rate"].iloc[0] == 13.56
    assert str(out["emp_length"].dtype) == "float64" and out["emp_length"].tolist() == [10, 0]
    assert pd.isna(out["annual_inc"].iloc[1])
    assert out["grade"].tolist() == ["B", "A"]  # whitespace stripped
    assert pd.isna(out["last_pymnt_d"].iloc[0])


def test_clean_loans_refuses_to_lose_a_value():
    raw = pd.DataFrame({"id": ["1", "2"], "annual_inc": ["50000", "n/a"]})
    with pytest.raises(ValueError, match="annual_inc"):
        clean_loans(raw)


def test_split_outcomes_separates_the_evaluation_columns():
    df = pd.DataFrame({"id": [1, 2], "loan_amnt": [100.0, 200.0], "total_pymnt": [110.0, 20.0]})
    features, outcomes = split_outcomes(df, ["total_pymnt"])
    assert list(features.columns) == ["id", "loan_amnt"]
    assert list(outcomes.columns) == ["id", "total_pymnt"]


# Loans written out of id order. With the default config only ids 1, 2, 3 and 5 are modelling
# loans: 4 is unresolved, 6 is a 60-month loan, 7 is a joint application, 8 was issued before
# 2013 and 9 after the test period.
RAW_CSV = (
    "id,issue_d,term,loan_status,application_type,loan_amnt,grade,total_pymnt\n"
    "5,Aug-2015, 36 months,Charged Off,Individual,5000,C,1200\n"
    "1,Jan-2013, 36 months,Fully Paid,Individual,1000,A,1100\n"
    "3,Jan-2015, 36 months,Fully Paid,Individual,3000,B,3300\n"
    "2,Jun-2013, 36 months,Charged Off,Individual,2000,B,500\n"
    "4,Jan-2015, 36 months,Current,Individual,4000,C,100\n"
    "6,Jan-2015, 60 months,Fully Paid,Individual,6000,C,7000\n"
    "7,Jan-2015, 36 months,Fully Paid,Joint App,7000,C,7700\n"
    "8,Dec-2012, 36 months,Fully Paid,Individual,8000,A,8800\n"
    "9,Jan-2016, 36 months,Charged Off,Individual,9000,A,100\n"
    "Total amount funded in policy code 1: 99,,,,,,,\n"
)
CLASSIFICATION_CSV = (
    "column,decision,reason,role,feature_set,in_app_model\n"
    "id,keep,x,identifier,,\n"
    "issue_d,keep,x,split_key,,\n"
    "term,keep,x,filter,,\n"
    "loan_status,keep,x,target,,\n"
    "application_type,keep,x,filter,,\n"
    "loan_amnt,keep,x,feature,core,yes\n"
    "grade,keep,x,feature,lc_assessment,no\n"
    "total_pymnt,eval_only,x,eval_only,,\n"
)


@pytest.fixture
def raw_parquet(tmp_path):
    csv_path = tmp_path / "loans.csv"
    csv_path.write_text(RAW_CSV, encoding="utf-8")
    parquet_path = tmp_path / "loans_raw.parquet"
    with duckdb.connect(":memory:") as source:
        load_raw_loans(source, csv_path)
        export_raw_loans_parquet(source, parquet_path)
    return parquet_path


def test_select_modelling_loans_applies_the_population_rules_in_id_order(raw_parquet):
    con = audit.open_raw_loans(raw_parquet)
    try:
        selected = clean.select_modelling_loans(con, ["id", "loan_amnt"])
    finally:
        con.close()
    assert selected["id"].tolist() == ["1", "2", "3", "5"]


def test_select_modelling_loans_names_a_missing_column(raw_parquet):
    con = audit.open_raw_loans(raw_parquet)
    try:
        with pytest.raises(ValueError, match="not_a_column"):
            clean.select_modelling_loans(con, ["id", "not_a_column"])
    finally:
        con.close()


def test_run_writes_a_features_table_and_a_separate_outcomes_table(raw_parquet, tmp_path):
    classification = tmp_path / "classification.csv"
    classification.write_text(CLASSIFICATION_CSV, encoding="utf-8")
    clean_path, outcomes_path = tmp_path / "out" / "clean.parquet", tmp_path / "out" / "outcomes.parquet"

    clean.run(raw_parquet, clean_path, outcomes_path, classification)

    features = pd.read_parquet(clean_path)
    outcomes = pd.read_parquet(outcomes_path)
    assert features["id"].tolist() == [1, 2, 3, 5]
    assert features[TARGET].tolist() == [0, 1, 0, 1]
    # features keep both feature sets; filters, the status text and the outcome never appear
    assert set(features.columns) == {"id", "issue_d", "loan_amnt", "grade", TARGET}
    assert list(outcomes.columns) == ["id", "total_pymnt"]
    assert outcomes["id"].tolist() == [1, 2, 3, 5]
    assert outcomes["total_pymnt"].tolist() == [1100.0, 500.0, 3300.0, 1200.0]
