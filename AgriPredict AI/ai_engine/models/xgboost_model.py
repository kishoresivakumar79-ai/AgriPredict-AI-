"""
XGBoost / Gradient Boosting Regressor Model.
Captures complex nonlinear relationships between weather, market arrivals,
demand shocks, and agricultural prices.
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
import joblib

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    from sklearn.ensemble import HistGradientBoostingRegressor, GradientBoostingRegressor

class AgriXGBoostModel:
    """
    Agricultural Price Prediction using Gradient Boosting / XGBoost.
    """
    def __init__(self, n_estimators: int = 150, learning_rate: float = 0.05, max_depth: int = 6):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.feature_names: List[str] = []
        self.model = None
        self.is_fitted = False
        self.backend = "xgboost" if HAS_XGBOOST else "hist_gradient_boosting"

        if HAS_XGBOOST:
            self.model = xgb.XGBRegressor(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                subsample=0.85,
                colsample_bytree=0.85,
                random_state=42,
                n_jobs=-1
            )
        else:
            self.model = GradientBoostingRegressor(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                subsample=0.85,
                random_state=42
            )

    def fit(self, X: pd.DataFrame, y: pd.Series, feature_names: Optional[List[str]] = None):
        """Fit the gradient boosting model on training data."""
        if feature_names is not None:
            self.feature_names = feature_names
        elif isinstance(X, pd.DataFrame):
            self.feature_names = list(X.columns)
        else:
            self.feature_names = [f"f_{i}" for i in range(X.shape[1])]

        X_mat = np.asarray(X)
        y_vec = np.asarray(y).ravel()
        self.model.fit(X_mat, y_vec)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict expected prices."""
        if not self.is_fitted:
            raise ValueError("Model is not fitted yet.")
        X_mat = np.asarray(X)
        return self.model.predict(X_mat)

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns sorted feature importance dictionary."""
        if not self.is_fitted:
            return {}
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            feat_imp = {name: float(imp) for name, imp in zip(self.feature_names, importances)}
            return dict(sorted(feat_imp.items(), key=lambda item: item[1], reverse=True))
        return {f: 1.0 / len(self.feature_names) for f in self.feature_names}

    def save(self, filepath: str):
        """Serializes model to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({"model": self.model, "feature_names": self.feature_names, "backend": self.backend}, filepath)

    def load(self, filepath: str):
        """Loads serialized model from disk."""
        data = joblib.load(filepath)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        self.backend = data.get("backend", "unknown")
        self.is_fitted = True
        return self

