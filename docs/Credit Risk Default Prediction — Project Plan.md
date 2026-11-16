# Credit Risk Default Prediction — Project Plan

Nov 15, 2026 · @Eva

## Project overview

An 8-week, end-to-end credit risk project that predicts which personal loans will default, explains why, and puts the results in an interactive Streamlit app.

**Business question:** *Which loan applicants are most likely to default, what drives that risk, and where should a lender set its approval cut-off to balance growth against losses?*

**Why this project for financial services:**

- Credit risk is core to retail banks, lenders and fintechs, so interviewers instantly understand the problem.
- It mirrors real work: messy data, regulatory-style documentation, model explainability and a business decision at the end.
- Explainability matters in UK finance (FCA Consumer Duty, model risk management), so SHAP explanations and a model card show you understand the context, not just the code.

**Final deliverables:**

1. A clean, reproducible GitHub repo with a one-command pipeline
2. SQL and Python data-cleaning pipeline with a documented cleaning log
3. Exploratory analysis with written business insights
4. A predictive model (baseline + gradient boosting) with SHAP explanations
5. A deployed Streamlit app: interactive charts, filterable tables and a "score an applicant" tool
6. A polished README, model card and data dictionary

## Goals

The project succeeds if a recruiter can open the repo, understand the business problem in 30 seconds, and click through to a working app.

**Portfolio goals**

- Show an employer you can take raw, messy data all the way to a business recommendation
- Have a live app link to put on your CV and LinkedIn
- Have a project you can talk through confidently for 10 minutes in an interview

**Technical goals**

- Build a reproducible pipeline: raw data → clean tables → features → model → app
- Write analysis queries in SQL (DuckDB) and reusable cleaning code in Python
- Train and compare at least two models using credit-industry metrics (AUC, Gini, KS)
- Explain the model globally and per applicant with SHAP
- Deploy an interactive Streamlit app with Plotly charts
- Write unit tests for the cleaning and feature code

**Learning goals**

- Spotting and preventing data leakage
- Time-based (out-of-time) validation, as banks use
- Turning model output into a business decision (approval cut-off and expected profit)
- Packaging Python code properly (`src/` layout, `pyproject.toml`)

**Success criteria**

| Criterion | Target |
| --- | --- |
| Pipeline reruns from raw data with one command | Yes |
| Model beats logistic regression baseline on out-of-time test set | Higher AUC |
| Test-set AUC, headline model (no Lending Club grade, sub-grade, interest rate or instalment) | 0.68 or above (provisional: confirm after the first baseline run, then freeze before looking at the test set) |
| Test-set AUC, ablation (adds grade, sub-grade, interest rate and instalment) | 0.70 or above (typical range for this data is roughly 0.68–0.73) |
| Compact app model within a stated AUC gap of the full model | Report the gap in the model card |
| App deployed and publicly reachable | Live link in README |
| Every cleaning decision documented | `cleaning_log.md` complete |
| Tests pass | `pytest` green |

## Data

The main dataset is Lending Club's public accepted-loans file: 2,260,701 loans and 151 columns covering 2007 to Q4 2018 ([source](https://www.k-dense.ai/use-cases/lendingclub-36-month-loan-survival-analysis)). It is enriched with US state unemployment from FRED.

| Dataset | What it gives you | Where | Size / format |
| --- | --- | --- | --- |
| [Lending Club accepted loans 2007–2018Q4](https://www.kaggle.com/datasets/wordsforthewise/lending-club) | Loan terms, borrower profile, credit history, final loan status | Kaggle (free account) | About 1.6 GB CSV ([source](https://gegznav.github.io/ds-projects/lending-club)) |
| [Lending Club data dictionary](https://figshare.com/articles/dataset/Lending_club_dataset_description/20016077) | Meaning of every column | Figshare | Small .xlsx |
| [FRED state unemployment rates](https://fredaccount.stlouisfed.org/public/datalist/337) | Monthly, seasonally adjusted unemployment for 50 states + DC (series IDs like CAUR) | FRED (free API key or CSV download) | Small CSVs |
| [FRED national unemployment (UNRATE)](https://fred.stlouisfed.org/series/UNRATE) | Monthly US unemployment rate | FRED | Small CSV |

**How the datasets join:** each loan has an issue month (`issue_d`) and state (`addr_state`). Join the state unemployment rate for that month, so the model knows the economic conditions when the loan was made.

**Key fields to start with**

| Group | Example columns |
| --- | --- |
| Target | `loan_status` (Fully Paid, Charged Off, Default, Current…) |
| Loan terms | `loan_amnt`, `term`, `int_rate`, `installment`, `grade`, `sub_grade`, `purpose` |
| Borrower | `annual_inc`, `emp_length`, `home_ownership`, `verification_status`, `addr_state` |
| Credit history | `dti`, `fico_range_low`, `fico_range_high`, `earliest_cr_line`, `open_acc`, `revol_util`, `delinq_2yrs`, `pub_rec`, `inq_last_6mths` |
| Dates | `issue_d` |

**Known data issues to handle (great material for your cleaning log)**

- **Unresolved loans:** loans with status "Current" have no outcome yet and must be removed from modelling.
- **Unfinished loans bias recent years (confirmed in the audit):** the loans that have finished are skewed towards early defaulters and early prepayers. 36-month loans issued 2016 are only 72% resolved and show a 19.8% default rate against 14.9% for 2015. 60-month loans are less resolved still: 83% for 2014, 67% for 2015, 55% for 2016, falling to 10% for 2018. Only 36-month loans issued up to 2015 are fully matured, so the model is built and tested on those.
- **Structurally missing columns:** the bureau-snapshot columns (e.g. `tot_cur_bal`, `mort_acc`) are 100% empty for 2007–2011 and about half empty for 2012. Modelling therefore starts at 2013, and no missing-value flags are added to these columns (they would just encode the issue year).
- **Joint applications:** `application_type` is "Joint App" for 120,710 loans, none before 2015. Modelling uses Individual loans only.
- **Leakage columns:** many fields are only known after the loan is issued (e.g. `total_pymnt`, `recoveries`, `last_pymnt_d`, `out_prncp`, `last_fico_range_high`). They must be dropped or the model will cheat.
- **Heavy missingness:** many columns are mostly empty (e.g. joint-application and hardship fields).
- **Messy types:** the raw table is all text, so numbers such as `int_rate` and `revol_util` need casting (this version of the file has no `%` signs), `emp_length` is text ("10+ years"), and dates are text like "Dec-2015".
- **Outliers:** extreme `annual_inc` and `dti` values.
- **Policy changes over time:** Lending Club's lending criteria changed between years, so older and newer loans behave differently. This is why the test set is split by time.
- **Class imbalance:** defaults are the minority class (roughly 1 in 5 resolved loans; confirm in your audit).

**Fake data?** Not needed. Real data with real problems is more convincing to recruiters, and the cleaning work becomes part of your story.

## Tech stack and repo structure

Everything is free and Python-based, using tools you already know plus a few that are standard in industry.

| Area | Tools | Why |
| --- | --- | --- |
| Storage and SQL | DuckDB | Fast SQL on large CSV/Parquet files, no server needed |
| Data wrangling | pandas (or Polars), PyArrow | Cleaning and Parquet files |
| Modelling | scikit-learn, XGBoost or LightGBM | Baseline and gradient boosting |
| Explainability | SHAP | Global and per-applicant explanations |
| Charts | Plotly | Interactive charts that work in Streamlit |
| App | Streamlit, Streamlit Community Cloud | Interactive app, free hosting |
| Quality | pytest, ruff | Tests and linting |
| Packaging | `pyproject.toml`, `src/` layout | Shared code across notebooks, app and tests |

**Repo structure**

```
credit-risk-default-prediction/
├── data/                    # ignored by Git
│   ├── raw/                 # Lending Club download, untouched
│   ├── external/            # FRED macro data
│   ├── interim/             # cleaned, before features
│   └── processed/           # model-ready tables
├── sql/
│   ├── schema/              # CREATE TABLE scripts
│   └── analysis/            # EDA queries
├── src/credit_risk/
│   ├── config.py            # paths, constants, random seed
│   ├── data/                # ingest.py, clean.py, validate.py
│   ├── features/            # build_features.py
│   └── models/              # train.py, evaluate.py, explain.py, predict.py
├── notebooks/               # 01_data_audit, 02_eda, 03_model_experiments
├── models/                  # trained model file
├── app/
│   ├── streamlit_app.py
│   ├── pages/
│   └── data/                # small aggregated files (committed)
├── reports/                 # figures/, findings.md, model_card.md
├── docs/                    # data_dictionary.md, cleaning_log.md
├── tests/
├── run_pipeline.py
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

The raw data is too big for GitHub, so `data/` is ignored. The app reads small pre-aggregated files from `app/data/`, which are committed, so the deployed app works.

## Weekly plan

Eight weeks at roughly 5–8 hours a week, in four phases: foundations (weeks 1–3), analysis (week 4), modelling (weeks 5–6) and delivery (weeks 7–8). Tick tasks off as you go.

&#91;embedded content: project roadmap · 4 phases, 8 weeks, 3 gates\]

Don't start a phase until the gate before it is passed: a broken pipeline or leaky model makes everything after it wasted work.

### Week 1: Setup and scoping

**Goal:** a working repo and a clear problem statement.

- [x] Create the GitHub repo (README, Python `.gitignore`, MIT licence) and clone it in VS Code
- [x] Create the folder structure, virtual environment and `pyproject.toml`; run `pip install -e .`
- [ ] Download the Lending Club data and data dictionary; download FRED unemployment CSVs
- [ ] Write the README skeleton: business question, data sources, planned approach
- [ ] Write `config.py` with file paths and a fixed random seed

**Deliverable:** repo with structure, README v0.1. **Done when:** a fresh clone installs without errors.

### Week 2: Ingestion and data audit

**Goal:** understand exactly what is in the data before changing anything.

- [ ] `ingest.py`: load the raw CSV into DuckDB and save as Parquet (much faster to reload)
- [ ] `01_data_audit.ipynb`: row counts, column types, % missing per column, value counts of `loan_status`
- [ ] SQL queries in `sql/analysis/`: loans per year, status breakdown, default rate by grade
- [ ] Classify every column as *keep*, *drop: leakage*, *drop: too sparse* or *drop: irrelevant*
- [ ] Start `data_dictionary.md` and `cleaning_log.md`

**Deliverable:** audit notebook and column classification. **Done when:** you can state the row count, date range, default rate and top 5 data problems.

### Week 3: Cleaning and feature pipeline

**Goal:** a reproducible script that turns raw data into a model-ready table.

- [ ] `clean.py`: keep resolved loans only, create binary target (`1` = Charged Off/Default, `0` = Fully Paid)
- [ ] `clean.py`: restrict the modelling population to 36-month, Individual loans issued from 2013 (2007–2012 and 60-month loans stay available for EDA only); drop footer rows without a numeric `id`
- [ ] Apply `docs/column_classification.csv`: drop leakage, sparse, irrelevant and redundant columns; write the `eval_only` columns to a separate outcome table that is never joined to the feature matrix; fix types (cast numbers from text, `emp_length`, dates)
- [ ] Handle missing values and cap outliers (e.g. `annual_inc`, `dti`) — log each choice and why
- [ ] `build_features.py`: credit history length, loan-to-income, FICO midpoint, issue month (not issue year: trees cannot extrapolate to years they have not seen). Skip instalment-to-income in the headline model, because `installment` is calculated from the interest rate
- [ ] Join FRED state unemployment by `addr_state` and the month before `issue_d` (the current month is not published at application time)
- [ ] `validate.py`: checks for nulls in key fields, value ranges, duplicate IDs
- [ ] Write the first unit tests for cleaning functions
- [ ] `run_pipeline.py`: one command from raw to processed

**Deliverable:** processed Parquet table, passing tests. **Done when:** deleting `data/processed/` and rerunning recreates it identically.

### Week 4: Exploratory analysis and insights

**Goal:** find the story in the data and write it in plain English.

- [ ] `02_eda.ipynb`: default rate by grade, term, purpose, home ownership, employment length, state
- [ ] Default rate by issue year (vintage analysis) and against unemployment
- [ ] Distributions of income, DTI, interest rate, FICO for defaulters vs non-defaulters
- [ ] Correlation check between numeric features
- [ ] Write 5–8 headline findings in `reports/findings.md` (e.g. "60-month loans default X times more than 36-month loans")
- [ ] Save the best charts to `reports/figures/` for the README

**Deliverable:** EDA notebook and findings document. **Done when:** each finding has a number and a "so what" for a lender.

### Week 5: Baseline and main model

**Goal:** a trained model that beats a simple baseline on an honest test set.

- [ ] Time-based split: train on older loans, validate and test on the newest (see Modelling approach)
- [ ] Preprocessing pipeline: encoding categoricals, scaling for logistic regression
- [ ] Baseline: logistic regression
- [ ] Main model: XGBoost or LightGBM with early stopping
- [ ] Ablation: rerun both models with `grade`, `sub_grade`, `int_rate` and `installment` added (`feature_set = lc_assessment` in the column classification) and record the AUC lift
- [ ] Compact model: retrain on the 12 features marked `in_app_model = yes`, for the app only, and record its AUC gap to the full model
- [ ] Light hyperparameter tuning (randomised search or Optuna) on the validation set only
- [ ] `train.py` saves the final model to `models/`

**Deliverable:** trained baseline and main model. **Done when:** both are scored on the same untouched test set.

### Week 6: Evaluation, explainability and business decision

**Goal:** prove the model is useful and explain how it works.

- [ ] `evaluate.py`: ROC-AUC, Gini, KS, precision/recall, calibration plot, confusion matrix
- [ ] Compare baseline vs main model in one table
- [ ] SHAP: global feature importance, dependence plots for top features, explanations for 3 example applicants
- [ ] Profit curve: estimated profit at each approval cut-off, using realised cash flows from the outcome table (`funded_amnt`, `total_pymnt`, `recoveries`) on the test set; recommend one cut-off
- [ ] Fairness check: no protected characteristics used; check whether `addr_state` acts as a proxy (zip code is dropped); note that `emp_length` and credit history length may proxy for age
- [ ] Write `reports/model_card.md`: purpose, data, metrics, limitations, intended use

**Deliverable:** evaluation report and model card. **Done when:** you can explain in 2 minutes why the model predicts what it does and what cut-off you would choose.

### Week 7: Streamlit app and deployment

**Goal:** a live, interactive app anyone can use.

- [ ] Export small aggregated tables and a sample of loans to `app/data/`
- [ ] **Overview page:** KPI tiles (loans, total lent, default rate) and default trend over time
- [ ] **Explore page:** filters (grade, purpose, term, state, year) driving Plotly charts and a filterable, downloadable table
- [ ] **Model page:** metrics, ROC curve, SHAP importance, profit curve with a cut-off slider
- [ ] **Score an applicant page:** a form with the 12 compact-model inputs (loan amount, purpose, income, DTI, FICO low and high, employment length, home ownership, earliest credit line, revolving utilisation, delinquencies, recent inquiries) → probability of default, risk band and SHAP explanation, from the compact model
- [ ] Cache data and model loading (`st.cache_data`, `st.cache_resource`)
- [ ] Deploy to Streamlit Community Cloud and test the live link

**Deliverable:** deployed app. **Done when:** the live link works in a private browser window.

### Week 8: Documentation and polish

**Goal:** make the repo recruiter-ready.

- [ ] Final README (see checklist below) with screenshots or a GIF of the app
- [ ] Tidy notebooks: clear headings, markdown commentary, outputs kept
- [ ] Run `ruff` and `pytest`; fix issues
- [ ] Ask a friend or colleague to clone and run it; fix whatever confuses them
- [ ] Pin the repo on your GitHub profile; add the app link to your CV and LinkedIn

**Deliverable:** finished portfolio project. **Done when:** someone else can understand and run it without asking you anything.

## Modelling approach

The model predicts the probability that a loan defaults, using only information available on the day of application, and is tested on later loans it has never seen.

**Target:** `1` if `loan_status` is Charged Off or Default, `0` if Fully Paid. Drop Current, Late and In Grace Period loans (no final outcome). Note that some files include "Does not meet the credit policy" prefixed statuses; map them to the same two outcomes.

**Preventing leakage:** for every feature, ask *"Would the lender know this on the application date?"* If not, drop it. `grade`, `sub_grade` and `int_rate` are Lending Club's own risk assessment, so including them means partly copying their model. **Decision:** the headline model excludes them, and also excludes `installment`, which is calculated from the loan amount, term and interest rate, so with a fixed term it would reveal the rate. An ablation run adds them back, and the AUC difference is reported as a finding. Every column's decision, role and feature set is recorded in `docs/column_classification.csv`.

**Outcome table:** columns that are only known after the loan is issued but are needed for evaluation (`funded_amnt`, `total_pymnt`, `total_rec_prncp`, `total_rec_int`, `recoveries`, `collection_recovery_fee`, `last_pymnt_d`) are kept in a separate table for the profit curve and are never part of the feature matrix.

**Train/test split (out-of-time):**

Population: 36-month, Individual loans with a final outcome, issued from 2013.

| Set | Loans issued | Loans | Default rate | Use |
| --- | --- | --- | --- | --- |
| Train | Jan 2013 – Dec 2014 | 262,992 | 13.2% | Fit models |
| Validation | Jan – Jun 2015 | 120,790 | 15.1% | Tune and pick the model |
| Test | Jul – Dec 2015 | 161,997 | 14.7% | Final score, used once |

Counts are from the audit; recheck them after `clean.py`. All three sets are fully matured (a 36-month loan issued in December 2015 ends in December 2018, the end of the data), so their default rates are comparable. Loans issued in 2016 or later, and all 60-month loans, are excluded because many are still unresolved and their default rate is biased. Validation and test are adjacent six-month windows, so mention this as a limitation next to the out-of-time claim.

**Models:**

1. Logistic regression (baseline, easy to explain, similar to traditional credit scorecards)
2. XGBoost or LightGBM (usually stronger on tabular data)

Each is trained as a headline version (no grade or rate) and an ablation version (with them). A third, compact version of the best model uses the 12 form-friendly features and powers the "Score an applicant" page. The full model gives the reported metrics.

**Metrics:**

| Metric | What it tells you |
| --- | --- |
| ROC-AUC | How well the model ranks risky above safe borrowers |
| Gini (2 × AUC − 1) | The ranking measure most used in UK credit risk teams |
| KS statistic | Maximum separation between good and bad score distributions |
| Precision / recall at cut-off | Trade-off between catching defaults and rejecting good customers |
| Calibration (Brier score, calibration plot) | Whether a predicted 20% really means about 20% default |

**Class imbalance:** use `scale_pos_weight` (XGBoost) or class weights rather than oversampling, and judge models with the metrics above, not accuracy.

**Explainability:** SHAP summary plot (which features matter most overall), dependence plots (how risk changes with e.g. DTI) and waterfall plots for individual applicants.

**Business decision:** use a simple profit model: realised profit per loan is `total_pymnt` minus `funded_amnt` from the outcome table. Rank test-set loans by predicted risk, plot total realised profit for each approval cut-off and recommend one. State your assumptions clearly (no funding or servicing costs, loans are independent, and approving a loan has no effect on its outcome).

## Risks and mitigations

The biggest risks are scope creep and data leakage; both are managed by finishing the core first and checking every feature against the application date.

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Scope creep (adding features before the core is done) | Project never finishes | Finish weeks 1–7 core tasks first; park ideas in a "Stretch goals" list |
| Data leakage | Unrealistically high AUC that interviewers will question | Leakage checklist per column; be suspicious of any AUC above about 0.80 |
| File too large for laptop memory | Crashes, slow work | Use DuckDB and Parquet; load only needed columns; develop on a sample first |
| Streamlit app fails on deployment | No live link | Commit only small files to `app/data/`; pin package versions in `requirements.txt`; deploy early in week 7 |
| Model file too large for GitHub | Push rejected | Keep the model under about 50 MB; reduce trees or use LightGBM's compact format |
| Falling behind schedule | Stress, rushed polish | Week 8 is a buffer; cut tuning or extra app pages before cutting documentation |
| Notebooks become messy | Repo looks unprofessional | Move reusable code into `src/` as soon as it works |
| Misleading conclusions from older vintages | Wrong insights | Use out-of-time testing; mention Lending Club policy changes in limitations |

## Presenting the project

Recruiters spend under a minute on a repo, so the README must show the problem, results and live app at the top.

**README checklist**

- [ ] Title and one-sentence summary
- [ ] Live app link and a screenshot or GIF near the top
- [ ] Business problem and why it matters
- [ ] Key results: test AUC/Gini, top 3 risk drivers, recommended cut-off
- [ ] 3–5 headline insights with one chart each
- [ ] Data sources with links and how to download them
- [ ] Pipeline diagram (raw → clean → features → model → app)
- [ ] How to run it: install, `python run_pipeline.py`, `streamlit run app/streamlit_app.py`
- [ ] Repo structure overview
- [ ] Limitations and next steps
- [ ] Tech stack badges or list

**Interview talking points to prepare**

- Why you chose out-of-time validation instead of a random split
- Which columns you removed for leakage and how you spotted them
- Why gradient boosting beat (or didn't beat) logistic regression
- What the top SHAP drivers were and whether they make business sense
- How you would choose an approval cut-off and what the trade-off is
- What you would change before using a model like this in a real bank (governance, monitoring, fairness, regulators)

**Stretch goals (only after the core is finished)**

- GitHub Actions to run `pytest` and `ruff` on every push
- A traditional scorecard using Weight of Evidence and points-based scoring
- Probability calibration (isotonic or Platt) and a calibration comparison
- Model monitoring demo: Population Stability Index (PSI) between train and test years
- Survival analysis: predicting *when* a loan defaults, not just whether
- Expected loss estimate: probability of default × exposure × loss given default

## Sources

- [Lending Club dataset on Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club)
- [Lending Club data dictionary (Figshare)](https://figshare.com/articles/dataset/Lending_club_dataset_description/20016077)
- [Lending Club file size and dimensions](https://gegznav.github.io/ds-projects/lending-club)
- [Lending Club row and column count](https://www.k-dense.ai/use-cases/lendingclub-36-month-loan-survival-analysis)
- [FRED state unemployment rates](https://fredaccount.stlouisfed.org/public/datalist/337)
- [FRED US unemployment rate (UNRATE)](https://fred.stlouisfed.org/series/UNRATE)
