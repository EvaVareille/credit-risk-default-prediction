import pandas as pd

from credit_risk.data.clean import parse_emp_length, parse_percent, standardise_column_names


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
