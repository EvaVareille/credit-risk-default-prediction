import duckdb
import pytest

from credit_risk.data.ingest import RAW_LOANS_TABLE, export_raw_loans_parquet, load_raw_loans

CSV_TEXT = (
    "id,int_rate,emp_length,issue_d\n"
    "1, 13.56%,10+ years,Dec-2015\n"
    "2,7.9%,< 1 year,Jan-2014\n"
    "Total amount funded in policy code 1: 123,,,\n"
)


@pytest.fixture
def con():
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def loans_csv(tmp_path):
    path = tmp_path / "loans.csv"
    path.write_text(CSV_TEXT, encoding="utf-8")
    return path


def test_load_raw_loans_keeps_every_row_as_text(con, loans_csv):
    n_rows = load_raw_loans(con, loans_csv)

    assert n_rows == 3  # two loans plus the footer line, untouched
    types = {name: dtype for name, dtype, *_ in con.execute(f"DESCRIBE {RAW_LOANS_TABLE}").fetchall()}
    assert set(types.values()) == {"VARCHAR"}
    assert con.execute(f"SELECT int_rate FROM {RAW_LOANS_TABLE} WHERE id = '1'").fetchone()[0] == " 13.56%"


def test_load_raw_loans_is_idempotent(con, loans_csv):
    load_raw_loans(con, loans_csv)

    assert load_raw_loans(con, loans_csv) == 3


def test_load_raw_loans_missing_file_raises(con, tmp_path):
    with pytest.raises(FileNotFoundError):
        load_raw_loans(con, tmp_path / "missing.csv")


def test_export_raw_loans_parquet_round_trips(con, loans_csv, tmp_path):
    load_raw_loans(con, loans_csv)
    parquet_path = tmp_path / "nested" / "loans.parquet"

    export_raw_loans_parquet(con, parquet_path)

    assert con.execute("SELECT count(*) FROM read_parquet(?)", [str(parquet_path)]).fetchone()[0] == 3
