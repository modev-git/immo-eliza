"""
predict/prediction.py

Loads the saved XGBoost pipeline and exposes a predict() function.

The model is loaded once at import time so repeated calls are fast.
"""

import os
import joblib
import pandas as pd

# Load model once
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "model.joblib")

try:
    _pipeline = joblib.load(_MODEL_PATH)
except FileNotFoundError:
    _pipeline = None   # will raise a clear error when predict() is called


# Public function

def predict(X: pd.DataFrame) -> float:
    """
    Run the saved pipeline on a preprocessed feature DataFrame.

    Returns
    -------
    float
        Predicted property price in EUR.

    Raises
    ------
    RuntimeError
        If the model file has not been generated yet.
    """
    if _pipeline is None:
        raise RuntimeError(
            "Model not found at 'model/model.pkl'. "
            "Run train_model.py first to generate it."
        )
    predicted = _pipeline.predict(X)
    return round(float(predicted[0]), 2)
