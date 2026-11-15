# credit-risk-default-prediction
Predicting loan defaults with Python, SQL, XGBoost and SHAP, with an interactive Streamlit app.

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
