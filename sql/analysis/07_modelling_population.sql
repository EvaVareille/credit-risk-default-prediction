-- How many loans survive each modelling filter, and the size and default rate of each split.
-- The filters and dates come from config.py ($model_term_months, $model_application_type,
-- $train_start, $validation_start, $test_start, $test_end); audit.run_sql_file supplies them.
-- Checks that the three splits have comparable default rates, and reproduces the counts in
-- docs/cleaning_log.md. Week 3's validate.py should assert the same on the cleaned table.
-- Needs the `loans_audit` view: audit.run_sql_file creates it (audit.create_audit_view).
WITH resolved AS (
    SELECT * FROM loans_audit WHERE outcome <> 'unresolved'
),
one_term AS (
    SELECT * FROM resolved WHERE term_months = $model_term_months
),
one_type AS (
    SELECT * FROM one_term WHERE application_type = $model_application_type
),
from_start AS (
    SELECT
        *,
        CASE
            WHEN issue_date >= $test_end        THEN 'after test (excluded)'
            WHEN issue_date >= $test_start      THEN 'test'
            WHEN issue_date >= $validation_start THEN 'validation'
            ELSE 'train'
        END AS split
    FROM one_type
    WHERE issue_date >= $train_start
)
SELECT 1 AS step_no, 'All loan rows' AS step, COUNT(*) AS n_loans, NULL AS default_rate
FROM loans_audit
UNION ALL
SELECT 2, 'Resolved (Fully Paid, Charged Off, Default)', COUNT(*), ROUND(AVG(is_default), 4)
FROM resolved
UNION ALL
SELECT 3, '... and the modelling term', COUNT(*), ROUND(AVG(is_default), 4)
FROM one_term
UNION ALL
SELECT 4, '... and the modelling application type', COUNT(*), ROUND(AVG(is_default), 4)
FROM one_type
UNION ALL
SELECT 5, '... and issued from the training start', COUNT(*), ROUND(AVG(is_default), 4)
FROM from_start
UNION ALL
SELECT 6, 'Train', COUNT(*), ROUND(AVG(is_default), 4) FROM from_start WHERE split = 'train'
UNION ALL
SELECT 7, 'Validation', COUNT(*), ROUND(AVG(is_default), 4) FROM from_start WHERE split = 'validation'
UNION ALL
SELECT 8, 'Test', COUNT(*), ROUND(AVG(is_default), 4) FROM from_start WHERE split = 'test'
UNION ALL
SELECT 9, 'Issued after the test period (excluded)', COUNT(*), ROUND(AVG(is_default), 4)
FROM from_start WHERE split = 'after test (excluded)'
ORDER BY step_no;
