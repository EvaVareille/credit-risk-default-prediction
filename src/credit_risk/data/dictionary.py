"""Build docs/data_dictionary.md from the column classification and the Lending Club dictionary.

The classification CSV decides which columns appear and how they are grouped. The Lending
Club dictionary supplies the descriptions. The Parquet cache supplies each column's type.
Dropped columns are left out: docs/column_classification.csv already explains them.

Regenerate after changing the classification:  python -m credit_risk.data.dictionary
"""

import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from credit_risk.config import (
    COLUMN_CLASSIFICATION_CSV,
    DATA_DICTIONARY_MD,
    FEATURE_SET_CORE,
    FEATURE_SET_LC_ASSESSMENT,
    LC_DATA_DICTIONARY,
)

_XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_FIRST_SHEET = "xl/worksheets/sheet1.xml"  # the column list; later sheets are other tables
_TABLE_HEAD = "| Column | Type | Description | Source | Notes |\n| --- | --- | --- | --- | --- |"

# Core feature groups, taken from the first words of each column's classification reason.
_CORE_GROUPS = {
    "Loan terms": "Core features: loan terms",
    "Borrower profile": "Core features: borrower profile",
    "Credit history at application": "Core features: credit history at application",
    "Bureau snapshot": "Core features: bureau snapshot (loans issued 2013 onward)",
    "Months since an event": "Core features: months since an event",
}

# Shorter or clearer than the Lending Club wording (which also has encoding damage).
_DESCRIPTION_OVERRIDES = {
    "dti": (
        "Monthly debt payments (excluding mortgage and the requested loan) divided by "
        "monthly income, at application."
    ),
    "emp_length": "Employment length in years (0 = under one year, 10 = ten or more years).",
    "home_ownership": "Home ownership status: RENT, OWN, MORTGAGE or OTHER.",
    "loan_amnt": "The amount of the loan applied for by the borrower.",
    "purpose": "The borrower's stated purpose for the loan (category).",
    "term": "Number of payments on the loan, in months (36 or 60).",
    "verification_status": (
        "Whether Lending Club verified the borrower's income: Verified, Source Verified "
        "or Not Verified."
    ),
    "fico_range_low": "Lower bound of the borrower's FICO range at loan origination.",
    "fico_range_high": "Upper bound of the borrower's FICO range at loan origination.",
    "issue_d": "Month the loan was funded.",
    "loan_status": "Current status of the loan.",
    "funded_amnt": "Total amount committed to the loan at funding.",
}

_FILTER_AND_KEY_NOTES = {
    "id": (
        "Identifier, not a feature. Used for the duplicate-ID check. Rows without a "
        "numeric `id` are footer lines and are dropped"
    ),
    "loan_status": (
        "Source of the target. Fully Paid and Charged Off/Default (including the "
        '"Does not meet the credit policy" versions) are kept; every other status is dropped'
    ),
    "issue_d": (
        "Split key and join key for the unemployment data. Not a model feature; only the "
        "issue month is derived from it"
    ),
    "term": (
        "Filter: modelling uses 36-month loans only, so it is constant and not a feature. "
        "Used in the profit calculation"
    ),
    "application_type": (
        "Filter: modelling uses Individual loans only, so it is constant and not a feature"
    ),
}

_ABLATION_NOTES = {
    "installment": "calculated from loan amount, term and rate, so it reveals the rate",
    "int_rate": "Lending Club's own risk pricing",
    "grade": "Lending Club's own risk assessment",
    "sub_grade": "Lending Club's own risk assessment",
}

_OUTCOME_NOTES = {
    "funded_amnt": "exposure per loan",
    "total_pymnt": "realised profit = `total_pymnt` minus `funded_amnt`",
    "total_rec_prncp": "realised loss given default",
    "total_rec_int": "realised interest income",
    "recoveries": "recovery rate after charge-off",
    "collection_recovery_fee": "collection costs netted off recoveries",
    "last_pymnt_d": "checks for unresolved loans; survival-analysis stretch goal",
}

_DERIVED_ROWS = (
    (
        "| `credit_history_years` | float | Years from `earliest_cr_line` to `issue_d` "
        "| Derived | Core; app; possible age proxy |"
    ),
    "| `loan_to_income` | float | `loan_amnt` divided by `annual_inc` | Derived | Core |",
    (
        "| `fico_mid` | float | Midpoint of `fico_range_low` and `fico_range_high` "
        "| Derived | Core; app |"
    ),
    (
        "| `issue_month` | int | Calendar month of `issue_d` (1-12). The year is deliberately "
        "not used | Derived | Core |"
    ),
    (
        "| `state_unemployment_rate` | float | Seasonally adjusted unemployment rate (%) for "
        "`addr_state` in the month before `issue_d` | FRED | Core |"
    ),
)

_NOT_COLLECTED_BEFORE_2012 = frozenset(
    {"mths_since_last_major_derog", "mths_since_recent_bc_dlq", "mths_since_recent_revol_delinq"}
)
_AGE_PROXIES = frozenset({"emp_length", "earliest_cr_line"})
_FICO_BOUNDS = frozenset({"fico_range_low", "fico_range_high"})


def read_lc_descriptions(path: Path = LC_DATA_DICTIONARY) -> dict[str, str]:
    """Read column descriptions from the Lending Club .xlsx, keyed by lower-case column name.

    Uses only the standard library, so no spreadsheet package is needed.
    """
    with zipfile.ZipFile(path) as archive:
        shared = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        strings = [
            "".join(t.text or "" for t in item.iter(_XLSX_NS + "t"))
            for item in shared.findall(_XLSX_NS + "si")
        ]
        sheet = ET.fromstring(archive.read(_FIRST_SHEET))

    descriptions = {}
    for row in sheet.iter(_XLSX_NS + "row"):
        cells = {}
        for cell in row.findall(_XLSX_NS + "c"):
            column_letter = re.match(r"[A-Z]+", cell.get("r")).group()
            value = cell.find(_XLSX_NS + "v")
            if value is not None:
                cells[column_letter] = strings[int(value.text)] if cell.get("t") == "s" else value.text
        if cells.get("A") and cells.get("B"):
            # Some names carry stray characters (e.g. 'total_rev_hi_lim' plus a symbol).
            descriptions[re.sub(r"[^a-z0-9_]", "", cells["A"].lower())] = cells["B"]
    return descriptions


def clean_description(text: str) -> str:
    """Repair the encoding damage and stray whitespace in a Lending Club description."""
    text = text.replace("��", "").replace("�s", "'s").replace("�", " ")
    text = re.sub(r"\s+", " ", text).strip().rstrip("*").strip()
    return re.sub(r"\s+([,.;:])", r"\1", text)


def read_classification(path: Path = COLUMN_CLASSIFICATION_CSV) -> list[dict[str, str]]:
    """Read docs/column_classification.csv as a list of row dicts."""
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def column_type(column: str, inferred_type: str) -> str:
    """Name a column's type after cleaning, from the type the audit inferred for the raw text."""
    if column in ("id", "term"):
        return "int"
    if column == "emp_length":
        return "float"
    mapping = {"numeric": "float", "percent_text": "float", "mon_year_text": "date"}
    return mapping.get(inferred_type, "str")


def _source(column: str, inferred_type: str) -> str:
    cleaned = inferred_type in ("percent_text", "mon_year_text") or column in ("emp_length", "term")
    return "Lending Club, cleaned" if cleaned else "Lending Club"


def _core_group(row: dict[str, str]) -> str | None:
    return next((g for g in _CORE_GROUPS if row["reason"].startswith(g)), None)


def _core_note(row: dict[str, str]) -> str:
    column, group = row["column"], _core_group(row)
    notes = ["Core"]
    if row["in_app_model"] == "yes":
        notes.append("app")
    if group == "Bureau snapshot":
        notes.append("not collected before 2013")
    if group == "Months since an event":
        notes.append("missing mostly means the event never happened")
    if column in _NOT_COLLECTED_BEFORE_2012:
        notes.append("not collected before 2012")
    if column in _AGE_PROXIES:
        notes.append("possible age proxy")
    if column in _FICO_BOUNDS:
        notes.append("combined into a FICO midpoint")
    if column == "addr_state":
        notes.append("also the unemployment join key")
    return "; ".join(notes)


def build_markdown(
    classification: list[dict[str, str]],
    descriptions: dict[str, str],
    inferred_types: dict[str, str],
) -> str:
    """Return the data dictionary as Markdown. Raises if a described column has no description."""
    shown = [r for r in classification if r["role"] != "none"]
    missing = [r["column"] for r in shown if r["column"] not in descriptions
               and r["column"] not in _DESCRIPTION_OVERRIDES]
    if missing:
        raise ValueError(f"No description for: {', '.join(missing)}")

    def line(column: str, note: str) -> str:
        text = _DESCRIPTION_OVERRIDES.get(column) or clean_description(descriptions[column])
        inferred = inferred_types[column]
        return (f"| `{column}` | {column_type(column, inferred)} | {text} "
                f"| {_source(column, inferred)} | {note} |")

    features = [r for r in classification if r["role"] == "feature"]
    lines = [
        "# Data Dictionary",
        "",
        (
            "Describes the columns the model and the app use. Every raw column, including the "
            "dropped ones, has a decision and a reason in "
            "[column_classification.csv](column_classification.csv); this file does not repeat "
            "the dropped ones. Descriptions come from the Lending Club data dictionary, "
            "shortened. Types are the types after cleaning."
        ),
        "",
        (
            "**Modelling population:** 36-month, Individual loans with a final outcome, issued "
            "from 2013 (see [cleaning_log.md](cleaning_log.md))."
        ),
        "",
        (
            f"**Feature sets:** `{FEATURE_SET_CORE}` columns make up the headline model. "
            f"`{FEATURE_SET_LC_ASSESSMENT}` columns are added only in the ablation run. The "
            '`app` note marks the 12 columns behind the compact model on the "Score an '
            'applicant" page (two of them, the FICO bounds, enter the model as one midpoint).'
        ),
        "",
        "## Identifiers, target and filters",
        "",
        _TABLE_HEAD,
    ]
    for column in ("id", "loan_status"):
        lines.append(line(column, _FILTER_AND_KEY_NOTES[column]))
    lines.append("| `is_default` | int | 1 = Charged Off or Default, 0 = Fully Paid | Derived | The target |")
    for column in ("issue_d", "term", "application_type"):
        lines.append(line(column, _FILTER_AND_KEY_NOTES[column]))
    lines.append("")

    for group, title in _CORE_GROUPS.items():
        lines += [f"## {title}", "", _TABLE_HEAD]
        lines += [line(r["column"], _core_note(r)) for r in features
                  if r["feature_set"] == FEATURE_SET_CORE and _core_group(r) == group]
        lines.append("")

    lines += [
        "## Ablation features (Lending Club's own assessment)",
        "",
        "Excluded from the headline model; added only to measure how much they lift AUC.",
        "",
        _TABLE_HEAD,
    ]
    lines += [line(r["column"], "Ablation only; " + _ABLATION_NOTES[r["column"]])
              for r in features if r["feature_set"] == FEATURE_SET_LC_ASSESSMENT]
    lines += [
        "",
        "## Derived features (planned)",
        "",
        "Names are provisional until `build_features.py` exists.",
        "",
        _TABLE_HEAD,
        *_DERIVED_ROWS,
        "",
        "## Outcome table (evaluation only)",
        "",
        (
            "Known only after the loan is issued. Stored separately, never joined to the "
            "feature matrix, and used for the profit curve and the unresolved-loan checks."
        ),
        "",
        _TABLE_HEAD,
    ]
    lines += [line(r["column"], "Evaluation only; " + _OUTCOME_NOTES[r["column"]])
              for r in classification if r["role"] == "eval_only"]
    return "\n".join(lines) + "\n"


def write_data_dictionary(output_path: Path = DATA_DICTIONARY_MD) -> Path:
    """Build the dictionary from the real project files and write it to `output_path`."""
    from credit_risk.data.audit import open_raw_loans, profile_columns

    profile = profile_columns(open_raw_loans())
    inferred_types = dict(zip(profile["column"], profile["inferred_type"], strict=True))
    markdown = build_markdown(read_classification(), read_lc_descriptions(), inferred_types)
    output_path.write_text(markdown, encoding="utf-8", newline="\n")
    return output_path


if __name__ == "__main__":
    print(f"Wrote {write_data_dictionary()}")
