-- Default rate by Lending Club grade, over all resolved loans.
-- Grade is Lending Club's own assessment, so a steady rise from A to G is expected.
-- Mixes all years and both terms; see 04_resolved_share_by_term_and_year.sql for the caveat.
-- Needs the `loans_audit` view: audit.run_sql_file creates it (audit.create_audit_view).
SELECT
    grade,
    COUNT(*)                    AS n_loans,
    ROUND(AVG(is_default), 4)   AS default_rate
FROM loans_audit
WHERE outcome <> 'unresolved'
GROUP BY grade
ORDER BY grade;
