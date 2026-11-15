"""Evaluate the trained model: ROC AUC, Gini, KS, calibration, metrics by grade."""


def gini(auc: float) -> float:
    """Gini coefficient from ROC AUC, the usual credit-risk convention."""
    return 2 * auc - 1


def run() -> None:
    """Pipeline entry point: write metrics and figures to reports/."""
    raise NotImplementedError("evaluate.run: implement after training")
