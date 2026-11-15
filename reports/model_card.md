# Model Card: Loan Default Prediction

## Purpose
Estimate the probability that a Lending Club loan defaults (charged off) at origination.

## Intended use / out of scope
- Intended: portfolio analysis and education/demonstration.
- Out of scope: real lending decisions.

## Data
- Source: Lending Club accepted loans, YYYY–YYYY.
- Target: `is_default` (see `src/credit_risk/config.py`). Loans with unknown outcomes are excluded.
- Train/test split: TODO (time-based recommended).

## Model
TODO: algorithm, key hyperparameters, features used.

## Performance
| Metric | Train | Test |
|---|---|---|
| ROC AUC | | |
| Gini | | |
| KS | | |

## Explainability
TODO: top SHAP drivers.

## Limitations and risks
- Selection bias: only accepted applications are observed (no reject inference).
- Macro conditions differ from the training period.
- TODO: fairness considerations.

## Monitoring
TODO: what would be monitored in production (PSI, default-rate drift).
