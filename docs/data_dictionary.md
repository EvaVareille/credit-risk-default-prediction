# Data Dictionary

Describes the columns the model and the app use. Every raw column, including the dropped ones, has a decision and a reason in [column_classification.csv](column_classification.csv); this file does not repeat the dropped ones. Descriptions come from the Lending Club data dictionary, shortened. Types are the types after cleaning.

**Modelling population:** 36-month, Individual loans with a final outcome, issued from 2013 (see [cleaning_log.md](cleaning_log.md)).

**Feature sets:** `core` columns make up the headline model. `lc_assessment` columns are added only in the ablation run. The `app` note marks the 12 columns behind the compact model on the "Score an applicant" page (two of them, the FICO bounds, enter the model as one midpoint).

## Identifiers, target and filters

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `id` | int | A unique LC assigned ID for the loan listing. | Lending Club | Identifier, not a feature. Used for the duplicate-ID check. Rows without a numeric `id` are footer lines and are dropped |
| `loan_status` | str | Current status of the loan. | Lending Club | Source of the target. Fully Paid and Charged Off/Default (including the "Does not meet the credit policy" versions) are kept; every other status is dropped |
| `is_default` | int | 1 = Charged Off or Default, 0 = Fully Paid | Derived | The target |
| `issue_d` | date | Month the loan was funded. | Lending Club, cleaned | Split key and join key for the unemployment data. Not a model feature; only the issue month is derived from it |
| `term` | int | Number of payments on the loan, in months (36 or 60). | Lending Club, cleaned | Filter: modelling uses 36-month loans only, so it is constant and not a feature. Used in the profit calculation |
| `application_type` | str | Indicates whether the loan is an individual application or a joint application with two co-borrowers | Lending Club | Filter: modelling uses Individual loans only, so it is constant and not a feature |

## Core features: loan terms

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `loan_amnt` | float | The amount of the loan applied for by the borrower. | Lending Club | Core; app |
| `purpose` | str | The borrower's stated purpose for the loan (category). | Lending Club | Core; app |

## Core features: borrower profile

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `emp_length` | float | Employment length in years (0 = under one year, 10 = ten or more years). | Lending Club, cleaned | Core; app; possible age proxy |
| `home_ownership` | str | Home ownership status: RENT, OWN, MORTGAGE or OTHER. | Lending Club | Core; app |
| `annual_inc` | float | The self-reported annual income provided by the borrower during registration. | Lending Club | Core; app |
| `verification_status` | str | Whether Lending Club verified the borrower's income: Verified, Source Verified or Not Verified. | Lending Club | Core |
| `addr_state` | str | The state provided by the borrower in the loan application | Lending Club | Core; also the unemployment join key |

## Core features: credit history at application

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `dti` | float | Monthly debt payments (excluding mortgage and the requested loan) divided by monthly income, at application. | Lending Club | Core; app |
| `delinq_2yrs` | float | The number of 30+ days past-due incidences of delinquency in the borrower's credit file for the past 2 years | Lending Club | Core; app |
| `earliest_cr_line` | date | The month the borrower's earliest reported credit line was opened | Lending Club, cleaned | Core; app; possible age proxy |
| `fico_range_low` | float | Lower bound of the borrower's FICO range at loan origination. | Lending Club | Core; app; combined into a FICO midpoint |
| `fico_range_high` | float | Upper bound of the borrower's FICO range at loan origination. | Lending Club | Core; app; combined into a FICO midpoint |
| `inq_last_6mths` | float | The number of inquiries in past 6 months (excluding auto and mortgage inquiries) | Lending Club | Core; app |
| `open_acc` | float | The number of open credit lines in the borrower's credit file. | Lending Club | Core |
| `pub_rec` | float | Number of derogatory public records | Lending Club | Core |
| `revol_bal` | float | Total credit revolving balance | Lending Club | Core |
| `revol_util` | float | Revolving line utilization rate, or the amount of credit the borrower is using relative to all available revolving credit. | Lending Club | Core; app |
| `total_acc` | float | The total number of credit lines currently in the borrower's credit file | Lending Club | Core |
| `collections_12_mths_ex_med` | float | Number of collections in 12 months excluding medical collections | Lending Club | Core |
| `acc_now_delinq` | float | The number of accounts on which the borrower is now delinquent. | Lending Club | Core |
| `chargeoff_within_12_mths` | float | Number of charge-offs within 12 months | Lending Club | Core |
| `delinq_amnt` | float | The past-due amount owed for the accounts on which the borrower is now delinquent. | Lending Club | Core |
| `pub_rec_bankruptcies` | float | Number of public record bankruptcies | Lending Club | Core |
| `tax_liens` | float | Number of tax liens | Lending Club | Core |

## Core features: bureau snapshot (loans issued 2013 onward)

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `tot_coll_amt` | float | Total collection amounts ever owed | Lending Club | Core; not collected before 2013 |
| `tot_cur_bal` | float | Total current balance of all accounts | Lending Club | Core; not collected before 2013 |
| `total_rev_hi_lim` | float | Total revolving high credit/credit limit | Lending Club | Core; not collected before 2013 |
| `acc_open_past_24mths` | float | Number of trades opened in past 24 months. | Lending Club | Core; not collected before 2013 |
| `avg_cur_bal` | float | Average current balance of all accounts | Lending Club | Core; not collected before 2013 |
| `bc_open_to_buy` | float | Total open to buy on revolving bankcards. | Lending Club | Core; not collected before 2013 |
| `bc_util` | float | Ratio of total current balance to high credit/credit limit for all bankcard accounts. | Lending Club | Core; not collected before 2013 |
| `mo_sin_old_il_acct` | float | Months since oldest bank installment account opened | Lending Club | Core; not collected before 2013 |
| `mo_sin_old_rev_tl_op` | float | Months since oldest revolving account opened | Lending Club | Core; not collected before 2013 |
| `mo_sin_rcnt_rev_tl_op` | float | Months since most recent revolving account opened | Lending Club | Core; not collected before 2013 |
| `mo_sin_rcnt_tl` | float | Months since most recent account opened | Lending Club | Core; not collected before 2013 |
| `mort_acc` | float | Number of mortgage accounts. | Lending Club | Core; not collected before 2013 |
| `mths_since_recent_bc` | float | Months since most recent bankcard account opened. | Lending Club | Core; not collected before 2013 |
| `mths_since_recent_inq` | float | Months since most recent inquiry. | Lending Club | Core; not collected before 2013 |
| `num_accts_ever_120_pd` | float | Number of accounts ever 120 or more days past due | Lending Club | Core; not collected before 2013 |
| `num_actv_bc_tl` | float | Number of currently active bankcard accounts | Lending Club | Core; not collected before 2013 |
| `num_actv_rev_tl` | float | Number of currently active revolving trades | Lending Club | Core; not collected before 2013 |
| `num_bc_sats` | float | Number of satisfactory bankcard accounts | Lending Club | Core; not collected before 2013 |
| `num_bc_tl` | float | Number of bankcard accounts | Lending Club | Core; not collected before 2013 |
| `num_il_tl` | float | Number of installment accounts | Lending Club | Core; not collected before 2013 |
| `num_op_rev_tl` | float | Number of open revolving accounts | Lending Club | Core; not collected before 2013 |
| `num_rev_accts` | float | Number of revolving accounts | Lending Club | Core; not collected before 2013 |
| `num_rev_tl_bal_gt_0` | float | Number of revolving trades with balance >0 | Lending Club | Core; not collected before 2013 |
| `num_sats` | float | Number of satisfactory accounts | Lending Club | Core; not collected before 2013 |
| `num_tl_120dpd_2m` | float | Number of accounts currently 120 days past due (updated in past 2 months) | Lending Club | Core; not collected before 2013 |
| `num_tl_30dpd` | float | Number of accounts currently 30 days past due (updated in past 2 months) | Lending Club | Core; not collected before 2013 |
| `num_tl_90g_dpd_24m` | float | Number of accounts 90 or more days past due in last 24 months | Lending Club | Core; not collected before 2013 |
| `num_tl_op_past_12m` | float | Number of accounts opened in past 12 months | Lending Club | Core; not collected before 2013 |
| `pct_tl_nvr_dlq` | float | Percent of trades never delinquent | Lending Club | Core; not collected before 2013 |
| `percent_bc_gt_75` | float | Percentage of all bankcard accounts > 75% of limit. | Lending Club | Core; not collected before 2013 |
| `tot_hi_cred_lim` | float | Total high credit/credit limit | Lending Club | Core; not collected before 2013 |
| `total_bal_ex_mort` | float | Total credit balance excluding mortgage | Lending Club | Core; not collected before 2013 |
| `total_bc_limit` | float | Total bankcard high credit/credit limit | Lending Club | Core; not collected before 2013 |
| `total_il_high_credit_limit` | float | Total installment high credit/credit limit | Lending Club | Core; not collected before 2013 |

## Core features: months since an event

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `mths_since_last_delinq` | float | The number of months since the borrower's last delinquency. | Lending Club | Core; missing mostly means the event never happened |
| `mths_since_last_record` | float | The number of months since the last public record. | Lending Club | Core; missing mostly means the event never happened |
| `mths_since_last_major_derog` | float | Months since most recent 90-day or worse rating | Lending Club | Core; missing mostly means the event never happened; not collected before 2012 |
| `mths_since_recent_bc_dlq` | float | Months since most recent bankcard delinquency | Lending Club | Core; missing mostly means the event never happened; not collected before 2012 |
| `mths_since_recent_revol_delinq` | float | Months since most recent revolving delinquency. | Lending Club | Core; missing mostly means the event never happened; not collected before 2012 |

## Ablation features (Lending Club's own assessment)

Excluded from the headline model; added only to measure how much they lift AUC.

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `int_rate` | float | Interest Rate on the loan | Lending Club | Ablation only; Lending Club's own risk pricing |
| `installment` | float | The monthly payment owed by the borrower if the loan originates. | Lending Club | Ablation only; calculated from loan amount, term and rate, so it reveals the rate |
| `grade` | str | LC assigned loan grade | Lending Club | Ablation only; Lending Club's own risk assessment |
| `sub_grade` | str | LC assigned loan subgrade | Lending Club | Ablation only; Lending Club's own risk assessment |

## Derived features (planned)

Names are provisional until `build_features.py` exists.

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `credit_history_years` | float | Years from `earliest_cr_line` to `issue_d` | Derived | Core; app; possible age proxy |
| `loan_to_income` | float | `loan_amnt` divided by `annual_inc` | Derived | Core |
| `fico_mid` | float | Midpoint of `fico_range_low` and `fico_range_high` | Derived | Core; app |
| `issue_month` | int | Calendar month of `issue_d` (1-12). The year is deliberately not used | Derived | Core |
| `state_unemployment_rate` | float | Seasonally adjusted unemployment rate (%) for `addr_state` in the month before `issue_d` | FRED | Core |
| `instalment_to_monthly_income` | float | `installment` divided by monthly income (`annual_inc` / 12) | Derived | Ablation only; reveals the interest rate |

## Outcome table (evaluation only)

Known only after the loan is issued. Stored separately, never joined to the feature matrix, and used for the profit curve and the unresolved-loan checks.

| Column | Type | Description | Source | Notes |
| --- | --- | --- | --- | --- |
| `funded_amnt` | float | Total amount committed to the loan at funding. | Lending Club | Evaluation only; exposure per loan |
| `total_pymnt` | float | Payments received to date for total amount funded | Lending Club | Evaluation only; realised profit = `total_pymnt` minus `funded_amnt` |
| `total_rec_prncp` | float | Principal received to date | Lending Club | Evaluation only; realised loss given default |
| `total_rec_int` | float | Interest received to date | Lending Club | Evaluation only; realised interest income |
| `recoveries` | float | post charge off gross recovery | Lending Club | Evaluation only; recovery rate after charge-off |
| `collection_recovery_fee` | float | post charge off collection fee | Lending Club | Evaluation only; collection costs netted off recoveries |
| `last_pymnt_d` | date | Last month payment was received | Lending Club, cleaned | Evaluation only; checks for unresolved loans; survival-analysis stretch goal |
