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
- Many columns are only known after the loan is issued (for example `total_pymnt`, `recoveries`). They are dropped to prevent leakage.
- Many columns are mostly empty.
- `int_rate` and `revol_util` are stored as strings with `%`, and `emp_length` is text.
- `annual_inc` and `dti` contain extreme outliers.
- Lending Club's criteria changed over time, so older and newer loans behave differently.
- Defaults are the minority class, roughly 1 in 5 resolved loans (to be confirmed in the data audit).

## Planned approach

1. **Ingest and audit.** Load the raw CSV into DuckDB, save as Parquet, and classify every column as keep, drop (leakage), drop (too sparse) or drop (irrelevant).
2. **Clean and build features.** Keep resolved loans only. Target is 1 for Charged Off or Default and 0 for Fully Paid. Fix types, handle missing values and outliers, add ratio and credit-history features, and join FRED unemployment. Validate the output and cover the cleaning code with unit tests.
3. **Explore.** Default rate by grade, term, purpose, state and issue year, written up as findings with a "so what" for a lender.
4. **Model.** Logistic regression baseline against XGBoost or LightGBM. Features are limited to information the lender would know on the application date. Models are trained with and without Lending Club's own `grade`, `sub_grade` and `int_rate` to measure how much they contribute.
5. **Validate out of time.** Train on the earliest years, tune on the next year, and score once on a later year, as banks do. A random split would overstate performance.
6. **Evaluate.** ROC-AUC, Gini, KS, precision and recall at a cut-off, and calibration. Class imbalance is handled with class weights, not oversampling.
7. **Explain.** SHAP global importance, dependence plots and per-applicant explanations. Check whether state acts as a proxy for a protected characteristic.
8. **Decide.** Plot expected profit at each approval cut-off and recommend one, with the assumptions stated.
9. **Deliver.** A Streamlit app with overview, explore and "score an applicant" pages, plus a model card and data dictionary.

Success criteria: the pipeline reruns from raw data with one command, the main model beats the baseline on the out-of-time test set with AUC of 0.70 or above, tests pass, and the app is publicly reachable.

## Project structure

```
data/            raw, external, interim and processed data (not committed)
sql/             EDA queries
src/credit_risk/ Python package: ingest, clean, validate, features, models, export
notebooks/       numbered notebooks: data audit, EDA, model experiments
models/          trained model file
app/             Streamlit app (app/data/ holds small committed aggregates)
reports/         figures, findings and model card
docs/            data dictionary and cleaning log
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
