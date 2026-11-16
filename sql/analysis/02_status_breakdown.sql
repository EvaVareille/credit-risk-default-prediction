-- Value counts of loan_status, with the outcome each status maps to in the target.
-- 'unresolved' loans have no final outcome and are dropped before modelling.
-- Needs the `loans_audit` view: audit.run_sql_file creates it (audit.create_audit_view).
SELECT
    loan_status                                         AS status,
    COUNT(*)                                            AS n_loans,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)  AS pct,
    outcome
FROM loans_audit
GROUP BY loan_status, outcome
ORDER BY n_loans DESC;
