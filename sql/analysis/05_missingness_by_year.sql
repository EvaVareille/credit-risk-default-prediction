-- Percent of loans with the column empty, by issue year, for columns whose availability changed.
-- Columns that are empty for whole years were not collected then, which is different from a
-- borrower leaving a field blank. `mths_since_last_delinq` is a control: it is partly empty
-- in every year because empty means the event never happened.
-- Decisions this supports: start modelling at 2013, and drop the columns first collected in
-- late 2015 (almost entirely empty for the training, validation and test periods).
-- Needs the `loans_audit` view: audit.run_sql_file creates it (audit.create_audit_view).
SELECT
    issue_year,
    COUNT(*)                                                                AS n_loans,
    ROUND(100.0 * AVG((tot_cur_bal IS NULL)::INT), 1)                       AS tot_cur_bal,
    ROUND(100.0 * AVG((mort_acc IS NULL)::INT), 1)                          AS mort_acc,
    ROUND(100.0 * AVG((mths_since_last_major_derog IS NULL)::INT), 1)       AS last_major_derog,
    ROUND(100.0 * AVG((mths_since_recent_bc_dlq IS NULL)::INT), 1)          AS recent_bc_dlq,
    ROUND(100.0 * AVG((mths_since_recent_revol_delinq IS NULL)::INT), 1)    AS recent_revol_delinq,
    ROUND(100.0 * AVG((open_acc_6m IS NULL)::INT), 1)                       AS open_acc_6m,
    ROUND(100.0 * AVG((il_util IS NULL)::INT), 1)                           AS il_util,
    ROUND(100.0 * AVG((inq_last_12m IS NULL)::INT), 1)                      AS inq_last_12m,
    ROUND(100.0 * AVG((mths_since_last_delinq IS NULL)::INT), 1)            AS last_delinq_control
FROM loans_audit
GROUP BY issue_year
ORDER BY issue_year;
