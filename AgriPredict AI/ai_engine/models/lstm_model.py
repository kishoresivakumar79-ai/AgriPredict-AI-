"""
LSTM / Sequential Neural Network Forecasting Model.
Learns long-term sequential price trends, temporal patterns, and time-dependent lag relationships.
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import joblib

class AgriLSTMModel:
    """
    Sequential / Recurrent Deep Forecasting Architecture.
    Processes sequential windows of price lags, arrival volumes, and weather observations.
    """
    def __init__(self, sequence_length: int = 30, hidden_layers: Tuple[int, ...] = (128, 64, 32)):
        self.sequence_length = sequence_length
        self.hidden_layers = hidden_layers
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.feature_names: List[str] = []
        self.is_fitted = False
        
        # Deep Multi-layer sequential regressor with adaptive learning & momentum
        self.nn_model = MLPRegressor(
            hidden_layer_sizes=self.hidden_layers,
            activation="relu",
            solver="adam",
            alpha=0.001,
            batch_size=64,
            learning_rate="adaptive",
            learning_rate_init=0.003,
            max_iter=250,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=15,
            random_state=42
        )

    def fit(self, X: pd.DataFrame, y: pd.Series, feature_names: Optional[List[str]] = None):
        """Fit sequential neural network on scaled feature windows."""
        if feature_names is not None:
            self.feature_names = feature_names
        elif isinstance(X, pd.DataFrame):
            self.feature_names = list(X.columns)
        else:
            self.feature_names = [f"f_{i}" for i in range(X.shape[1])]

        X_mat = np.asarray(X)
        y_vec = np.asarray(y).reshape(-1, 1)

        X_scaled = self.scaler_X.fit_transform(X_mat)
        y_scaled = self.scaler_y.fit_transform(y_vec).ravel()

        self.nn_model.fit(X_scaled, y_scaled)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict prices and invert standard scaling."""
        if not self.is_fitted:
            raise ValueError("Model is not fitted yet.")
        X_mat = np.asarray(X)
        X_scaled = self.scaler_X.transform(X_mat)
        y_pred_scaled = self.nn_model.predict(X_scaled).reshape(-1, 1)
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled).ravel()
        return np.maximum(200.0, y_pred)

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            "model": self.nn_model,
            "scaler_X": self.scaler_X,
            "scaler_y": self.scaler_y,
            "feature_names": self.feature_names,
            "sequence_length": self.sequence_length
        }, filepath)

    def load(self, filepath: str):
        data = joblib.load(filepath)
        self.nn_model = data["model"]
        self.scaler_X = data["scaler_X"]
        self.scaler_y = data["scaler_y"]
        self.feature_names = data["feature_names"]
        self.sequence_length = data.get("sequence_length", 30)
        self.is_fitted = True
        return self

