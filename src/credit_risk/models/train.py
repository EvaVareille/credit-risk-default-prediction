"""Train the default-prediction model (XGBoost) and save it to models/."""

from credit_risk.config import MODEL_PATH, RANDOM_SEED  # noqa: F401


def run() -> None:
    """Pipeline entry point: fit the model and save it to MODEL_PATH."""
    # TODO: time-based train/test split, baseline logistic regression, then XGBoost.
    raise NotImplementedError("train.run: implement after feature engineering")
