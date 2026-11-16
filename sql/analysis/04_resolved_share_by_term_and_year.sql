-- How much of each issue year and term has a final outcome, and the default rate among those.
-- Loans that are still running are missing from the default rate. The ones that have finished
-- skew towards early defaults and early repayments, so recent years look worse than they are.
-- Decision this supports: model 36-month loans only, and end the test set at 2015.
-- Needs the `loans_audit` view: audit.run_sql_file creates it (audit.create_audit_view).
SELECT
    issue_year,
    term_months,
    COUNT(*)                                                        AS n_loans,
    COUNT(*) FILTER (WHERE outcome <> 'unresolved')                 AS n_resolved,
    ROUND(100.0 * COUNT(*) FILTER (WHERE outcome <> 'unresolved') / COUNT(*), 1)
                                                                    AS pct_resolved,
    ROUND(AVG(is_default), 4)                                       AS default_rate
FROM loans_audit
GROUP BY issue_year, term_months
ORDER BY issue_year, term_months;
