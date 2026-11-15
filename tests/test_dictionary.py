import zipfile

import pytest

from credit_risk.data.dictionary import (
    build_markdown,
    clean_description,
    column_type,
    read_classification,
    read_lc_descriptions,
)


def _row(column, role="feature", feature_set="core", in_app="no", reason="Loan terms, known at application."):
    return {
        "column": column, "decision": "keep", "reason": reason, "role": role,
        "feature_set": feature_set, "in_app_model": in_app,
    }


CLASSIFICATION = [
    _row("id", role="identifier", feature_set="", reason="Identifier."),
    _row("loan_status", role="target", feature_set="", reason="Target."),
    _row("issue_d", role="split_key", feature_set="", reason="Split key."),
    _row("term", role="filter", feature_set="", reason="Filter."),
    _row("application_type", role="filter", feature_set="", reason="Filter."),
    _row("loan_amnt", in_app="yes"),
    _row("tot_cur_bal", reason="Bureau snapshot at application."),
    _row("int_rate", feature_set="lc_assessment"),
    _row("total_pymnt", role="eval_only", feature_set="", reason="Repayment history."),
    _row("member_id", role="none", feature_set="", reason="Empty in every row."),
]
DESCRIPTIONS = {"id": "Loan id", "application_type": "Individual or joint", "tot_cur_bal": "Total balance",
                "int_rate": "Interest rate", "total_pymnt": "Payments received"}
TYPES = {"id": "numeric", "loan_status": "text", "issue_d": "mon_year_text", "term": "text",
         "application_type": "text", "loan_amnt": "numeric", "tot_cur_bal": "numeric",
         "int_rate": "numeric", "total_pymnt": "numeric"}


def test_clean_description_repairs_encoding_and_spacing():
    raw = "The borrower�s  FICO  range� , at origination.*"
    assert clean_description(raw) == "The borrower's FICO range, at origination."


def test_column_type_after_cleaning():
    assert column_type("id", "numeric") == "int"
    assert column_type("term", "text") == "int"
    assert column_type("emp_length", "text") == "float"
    assert column_type("int_rate", "numeric") == "float"
    assert column_type("issue_d", "mon_year_text") == "date"
    assert column_type("purpose", "text") == "str"


def test_build_markdown_places_each_column_in_its_section():
    md = build_markdown(CLASSIFICATION, DESCRIPTIONS, TYPES)
    core_loan_terms = md.split("## Core features: loan terms")[1].split("## ")[0]
    assert "`loan_amnt`" in core_loan_terms and "Core; app" in core_loan_terms
    bureau = md.split("## Core features: bureau snapshot")[1].split("## ")[0]
    assert "`tot_cur_bal`" in bureau and "not collected before 2013" in bureau
    ablation = md.split("## Ablation features")[1].split("## ")[0]
    assert "`int_rate`" in ablation and "Ablation only" in ablation
    outcome = md.split("## Outcome table")[1]
    assert "`total_pymnt`" in outcome and "Evaluation only" in outcome
    assert "`is_default`" in md
    assert "member_id" not in md  # dropped columns are left out


def test_build_markdown_ends_with_single_newline():
    assert build_markdown(CLASSIFICATION, DESCRIPTIONS, TYPES).endswith("|\n")


def test_build_markdown_fails_loudly_on_missing_description():
    with pytest.raises(ValueError, match="int_rate"):
        build_markdown(CLASSIFICATION, {k: v for k, v in DESCRIPTIONS.items() if k != "int_rate"}, TYPES)


def test_read_lc_descriptions_from_a_minimal_xlsx(tmp_path):
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    strings = ["LoanStatNew", "Description", "Loan_Amnt ", "The amount", "total_rev_hi_lim�", "Limit"]
    shared = f'<sst {ns}>' + "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>"
    rows = "".join(
        f'<row><c r="A{i}" t="s"><v>{a}</v></c><c r="B{i}" t="s"><v>{b}</v></c></row>'
        for i, (a, b) in enumerate([(0, 1), (2, 3), (4, 5)], start=1)
    )
    path = tmp_path / "dict.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet1.xml", f"<worksheet {ns}><sheetData>{rows}</sheetData></worksheet>")
    assert read_lc_descriptions(path) == {
        "loanstatnew": "Description", "loan_amnt": "The amount", "total_rev_hi_lim": "Limit",
    }


def test_committed_classification_is_consistent():
    rows = read_classification()
    assert len({r["column"] for r in rows}) == len(rows), "duplicate column names"
    roles = {"feature", "target", "identifier", "split_key", "filter", "eval_only", "none"}
    for r in rows:
        assert r["role"] in roles, r["column"]
        assert (r["decision"] == "eval_only") == (r["role"] == "eval_only"), r["column"]
        if r["role"] == "feature":
            assert r["feature_set"] in {"core", "lc_assessment"}, r["column"]
            assert r["in_app_model"] in {"yes", "no"}, r["column"]
        else:
            assert r["feature_set"] == "" and r["in_app_model"] == "", r["column"]
        if r["role"] == "none":
            assert r["decision"].startswith("drop_"), r["column"]
