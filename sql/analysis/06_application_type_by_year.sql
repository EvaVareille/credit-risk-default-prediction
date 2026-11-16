-- Share of joint applications by issue year.
-- Joint applications start in 2015. On them annual_inc and dti describe one borrower while the
-- joint columns describe the pair, so their features mean something different.
-- Decision this supports: model Individual loans only.
-- Needs the `loans_audit` view: audit.run_sql_file creates it (audit.create_audit_view).
SELECT
    issue_year,
    COUNT(*)                                                        AS n_loans,
    COUNT(*) FILTER (WHERE application_type = 'Joint App')          AS n_joint,
    ROUND(100.0 * COUNT(*) FILTER (WHERE application_type = 'Joint App') / COUNT(*), 1)
                                                                    AS pct_joint
FROM loans_audit
GROUP BY issue_year
ORDER BY issue_year;
