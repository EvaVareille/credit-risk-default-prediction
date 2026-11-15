"""Load the trained model and score applicants. Used by the Streamlit app."""

from functools import lru_cache

import pandas as pd

from credit_risk.config import MODEL_PATH


@lru_cache(maxsize=1)
def load_model():
    """Load the saved model once and cache it."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No trained model at {MODEL_PATH}. Run run_pipeline.py first.")
    import xgboost as xgb

    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)
    return model


def predict_default_probability(applicants: pd.DataFrame) -> pd.Series:
    """Return the probability of default for each row."""
    model = load_model()
    return pd.Series(model.predict_proba(applicants)[:, 1], index=applicants.index, name="pd")
