-- Default rate by Lending Club grade.
SELECT
    grade,
    COUNT(*)                         AS n_loans,
    AVG(is_default)                  AS default_rate
FROM loans_model
GROUP BY grade
ORDER BY grade;
