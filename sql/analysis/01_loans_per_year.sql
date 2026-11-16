-- Loans, resolved loans and default rate by issue year.
-- Default rate is among resolved loans only (Fully Paid, Charged Off, Default).
-- Caution: recent years are only partly resolved, which biases their default rate.
-- See 04_resolved_share_by_term_and_year.sql.
-- Needs the `loans_audit` view: audit.run_sql_file creates it (audit.create_audit_view).
SELECT
    issue_year,
    COUNT(*)                                            AS n_loans,
    COUNT(*) FILTER (WHERE outcome = 'default')         AS n_default,
    COUNT(*) FILTER (WHERE outcome <> 'unresolved')     AS n_resolved,
    ROUND(AVG(is_default), 4)                           AS default_rate
FROM loans_audit
GROUP BY issue_year
ORDER BY issue_year;
