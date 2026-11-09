"""
Random Forest Regressor with Ensemble Uncertainty Bounds.
Calculates expected price and estimates confidence intervals across individual tree estimates.
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
from sklearn.ensemble import RandomForestRegressor
import joblib

class AgriRandomForestModel:
    """
    Random Forest Model with uncertainty quantification for agriculture price risk analysis.
    """
    def __init__(self, n_estimators: int = 100, max_depth: int = 14, min_samples_split: int = 4):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.feature_names: List[str] = []
        self.is_fitted = False
        
        self.rf = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            n_jobs=-1,
            random_state=42
        )

    def fit(self, X: pd.DataFrame, y: pd.Series, feature_names: Optional[List[str]] = None):
        """Fit Random Forest ensemble."""
        if feature_names is not None:
            self.feature_names = feature_names
        elif isinstance(X, pd.DataFrame):
            self.feature_names = list(X.columns)
        else:
            self.feature_names = [f"f_{i}" for i in range(X.shape[1])]

        X_mat = np.asarray(X)
        y_vec = np.asarray(y).ravel()
        self.rf.fit(X_mat, y_vec)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict expected price."""
        if not self.is_fitted:
            raise ValueError("Model is not fitted yet.")
        X_mat = np.asarray(X)
        return self.rf.predict(X_mat)

    def predict_with_confidence(
        self,
        X: pd.DataFrame,
        confidence_z: float = 1.645
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates expected, optimistic (90th percentile), and pessimistic (10th percentile) prices
        using the variance across the ensemble of decision trees.
        """
        if not self.is_fitted:
            raise ValueError("Model is not fitted yet.")
        X_mat = np.asarray(X)
        
        # Collect predictions from each individual estimator
        all_tree_preds = np.array([tree.predict(X_mat) for tree in self.rf.estimators_])
        
        expected = np.mean(all_tree_preds, axis=0)
        tree_std = np.std(all_tree_preds, axis=0)

        optimistic = expected + (confidence_z * tree_std)
        pessimistic = np.maximum(0.0, expected - (confidence_z * tree_std))

        return expected, optimistic, pessimistic

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns feature importances sorted descending."""
        if not self.is_fitted:
            return {}
        imps = self.rf.feature_importances_
        res = {name: float(val) for name, val in zip(self.feature_names, imps)}
        return dict(sorted(res.items(), key=lambda item: item[1], reverse=True))

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({"rf": self.rf, "feature_names": self.feature_names}, filepath)

    def load(self, filepath: str):
        data = joblib.load(filepath)
        self.rf = data["rf"]
        self.feature_names = data["feature_names"]
        self.is_fitted = True
        return self
