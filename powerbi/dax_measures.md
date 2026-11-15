# DAX Measures

Each measure, its DAX, and what it means for the business.

> Save the report as `powerbi/credit_risk.pbix` and screenshots in `powerbi/screenshots/`.

| Measure | DAX | Business meaning |
|---|---|---|
| Total Loans | `COUNTROWS(fact_loans)` | Number of loans in the selected portfolio |
| Default Rate | `DIVIDE(SUM(fact_loans[is_default]), [Total Loans])` | Share of loans that defaulted |
| TODO | | |
