-- Star schema for Power BI. Run against data/processed/credit_risk.duckdb.
-- TODO: finalise columns once cleaning is done.

-- CREATE TABLE dim_date (date_key INTEGER PRIMARY KEY, date DATE, year INTEGER, quarter INTEGER, month INTEGER);
-- CREATE TABLE dim_grade (grade_key INTEGER PRIMARY KEY, grade VARCHAR, sub_grade VARCHAR);
-- CREATE TABLE dim_borrower (borrower_key INTEGER PRIMARY KEY, home_ownership VARCHAR, emp_length DOUBLE, addr_state VARCHAR);
-- CREATE TABLE fact_loans (loan_id BIGINT PRIMARY KEY, issue_date_key INTEGER, grade_key INTEGER, borrower_key INTEGER,
--                          loan_amnt DOUBLE, int_rate DOUBLE, is_default TINYINT, predicted_pd DOUBLE);
