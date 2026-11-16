# credit-risk-default-prediction
Predicting loan defaults with Python, SQL, XGBoost and SHAP, with an interactive Streamlit app.

## Business question

Which loan applicants are most likely to default, what drives that risk, and where should a lender set its approval cut-off to balance growth against losses?

The project takes raw, messy lending data through to a business recommendation: a default-probability model, an explanation of why it predicts what it does, and a recommended approval cut-off backed by a simple profit model.

## Data sources

| Dataset | What it provides | Source |
|---|---|---|
| Lending Club accepted loans, 2007 to 2018 Q4 | Loan terms, borrower profile, credit history and final loan status. About 2.26 million loans and 151 columns (about 1.6 GB CSV). | [Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club) |
| Lending Club data dictionary | Meaning of every column | [Figshare](https://figshare.com/articles/dataset/Lending_club_dataset_description/20016077) |
| US state unemployment rates | Monthly, seasonally adjusted, 50 states plus DC | [FRED](https://fredaccount.stlouisfed.org/public/datalist/337) |
| US national unemployment rate (UNRATE) | Monthly national rate | [FRED](https://fred.stlouisfed.org/series/UNRATE) |

Each loan is joined to the state unemployment rate for its issue month (`issue_d`, `addr_state`), so the model sees the economic conditions when the loan was made.

The raw data is too large for GitHub and is not committed. Download it into `data/raw/` and run `run_pipeline.py`.

Known data issues, each recorded in `docs/cleaning_log.md`:

- Loans with status "Current" have no outcome yet and are removed from modelling.
- Recent loans are only partly resolved, and the ones that have finished skew towards early defaults. For example, 36-month loans issued in 2016 are 72% resolved and show a 19.8% default rate against 14.9% for 2015. Modelling therefore uses 36-month loans issued up to 2015, which are fully matured.
- Bureau-snapshot columns (for example `tot_cur_bal`, `mort_acc`) are empty for 2007 to 2011 and half empty for 2012, so modelling starts at 2013. Joint applications only start in 2015, so modelling uses Individual loans only.
- Many columns are only known after the loan is issued (for example `total_pymnt`, `recoveries`). They are never used as features. A few are kept in a separate outcome table to compute realised profit for the profit curve.
- Many columns are mostly empty.
- The raw table is all text, so numbers such as `int_rate` and `revol_util` need casting (no `%` signs in this file), and `emp_length` is text.
- `annual_inc` and `dti` contain extreme outliers.
- Lending Club's criteria changed over time, so older and newer loans behave differently.
- Defaults are the minority class: about 20% of resolved loans (269,360 of 1,348,099).

## Planned approach

1. **Ingest and audit.** Load the raw CSV into DuckDB, save as Parquet, and classify every column in `docs/column_classification.csv`: keep, drop (leakage, too sparse, irrelevant or redundant), or evaluation only.
2. **Clean and build features.** Keep resolved, 36-month, Individual loans issued from 2013 (60-month loans and loans from 2016 are only partly resolved, which biases their default rate). Target is 1 for Charged Off or Default and 0 for Fully Paid. Fix types, handle missing values and outliers, add ratio and credit-history features, and join FRED unemployment for the month before issue. Keep the post-issue columns needed for the profit curve in a separate outcome table. Validate the output and cover the cleaning code with unit tests.
3. **Explore.** Default rate by grade, term, purpose, state and issue year, written up as findings with a "so what" for a lender.
4. **Model.** Logistic regression baseline against XGBoost or LightGBM. Features are limited to information the lender would know on the application date. The headline models exclude Lending Club's own `grade`, `sub_grade` and `int_rate`, and also `installment`, which reveals the rate. An ablation adds them back to measure how much they contribute. A compact 12-feature model powers the app's scoring form.
5. **Validate out of time.** Train on loans issued 2013 to 2014, tune on the first half of 2015, and score once on the second half of 2015, as banks do. These are the latest fully matured 36-month loans. A random split would overstate performance.
6. **Evaluate.** ROC-AUC, Gini, KS, precision and recall at a cut-off, and calibration. Class imbalance is handled with class weights, not oversampling.
7. **Explain.** SHAP global importance, dependence plots and per-applicant explanations. Check whether state acts as a proxy for a protected characteristic, and note that employment length and credit history length may proxy for age.
8. **Decide.** Plot profit at each approval cut-off, using the realised repayments of the test loans, and recommend one, with the assumptions stated.
9. **Deliver.** A Streamlit app with overview, explore and "score an applicant" pages, plus a model card and data dictionary.

Success criteria: the pipeline reruns from raw data with one command, the headline model beats the baseline on the out-of-time test set (provisional target AUC of 0.68 or above without Lending Club's own grade and rate, 0.70 or above with them), tests pass, and the app is publicly reachable.

## Project structure

```
data/            raw, external, interim and processed data (not committed)
sql/             EDA queries
src/credit_risk/ Python package: ingest, clean, validate, features, models, export
notebooks/       numbered notebooks: data audit, EDA, model experiments
models/          trained model file
app/             Streamlit app (app/data/ holds small committed aggregates)
reports/         figures, findings and model card
docs/            project plan, column classification, data dictionary and cleaning log
tests/           unit tests
```

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt  # also installs this package in editable mode
pytest                           # run the tests
python run_pipeline.py           # rebuild all outputs from data/raw/
streamlit run app/streamlit_app.py
```

Raw data is never edited: every output can be rebuilt from `data/raw/` by running `run_pipeline.py`.
