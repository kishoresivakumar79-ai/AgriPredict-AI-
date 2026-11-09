"""
Prophet-Style Generalized Additive Time-Series Model for Agriculture.
Decomposes price time-series into:
y(t) = Trend(t) + Seasonality(t) + HolidayEffects(t) + WeatherEffects(t) + Noise
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
from sklearn.linear_model import Ridge
import joblib

class AgriProphetModel:
    """
    Decomposable Generalized Additive Model (GAM) for agricultural trend and seasonality.
    """
    def __init__(self, fourier_order_year: int = 5, fourier_order_week: int = 3, l2_reg: float = 1.0):
        self.fourier_order_year = fourier_order_year
        self.fourier_order_week = fourier_order_week
        self.l2_reg = l2_reg
        self.regressor = Ridge(alpha=self.l2_reg)
        self.base_date: Optional[pd.Timestamp] = None
        self.feature_names: List[str] = []
        self.is_fitted = False

    def _extract_gam_features(self, dates: pd.Series, additional_features: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Extracts trend time counter, annual Fourier terms, and weekly Fourier terms."""
        dts = pd.to_datetime(dates)
        if self.base_date is None:
            self.base_date = dts.min()

        # Trend term: normalized time days
        t_days = (dts - self.base_date).dt.total_seconds() / (24 * 3600.0)
        t_normalized = (t_days / 365.25).values.reshape(-1, 1)

        cols = [t_normalized]

        # Annual Fourier harmonics: period = 365.25
        doy = dts.dt.dayofyear.values
        for n in range(1, self.fourier_order_year + 1):
            cos_term = np.cos(2 * np.pi * n * doy / 365.25).reshape(-1, 1)
            sin_term = np.sin(2 * np.pi * n * doy / 365.25).reshape(-1, 1)
            cols.extend([cos_term, sin_term])

        # Weekly Fourier harmonics: period = 7
        dow = dts.dt.dayofweek.values
        for n in range(1, self.fourier_order_week + 1):
            cos_w = np.cos(2 * np.pi * n * dow / 7.0).reshape(-1, 1)
            sin_w = np.sin(2 * np.pi * n * dow / 7.0).reshape(-1, 1)
            cols.extend([cos_w, sin_w])

        # Major agricultural festivals / holidays in India (Pongal Jan 13-17, Diwali Oct/Nov)
        month = dts.dt.month.values
        day = dts.dt.day.values
        pongal = ((month == 1) & (day >= 13) & (day <= 17)).astype(float).reshape(-1, 1)
        diwali = ((np.isin(month, [10, 11])) & (day >= 20) & (day <= 30)).astype(float).reshape(-1, 1)
        cols.extend([pongal, diwali])

        X_gam = np.hstack(cols)

        if additional_features is not None:
            add_mat = np.asarray(additional_features)
            X_gam = np.hstack([X_gam, add_mat])

        return X_gam

    def fit(self, dates: pd.Series, y: pd.Series, additional_features: Optional[pd.DataFrame] = None):
        """Fit Prophet GAM model."""
        X = self._extract_gam_features(dates, additional_features)
        self.regressor.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, dates: pd.Series, additional_features: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Forecast prices across dates."""
        if not self.is_fitted:
            raise ValueError("Model is not fitted yet.")
        X = self._extract_gam_features(dates, additional_features)
        pred = self.regressor.predict(X)
        return np.maximum(200.0, pred)

    def decompose(self, dates: pd.Series) -> Dict[str, np.ndarray]:
        """Returns decomposed trend, annual seasonality, and weekly seasonality."""
        if not self.is_fitted:
            raise ValueError("Model is not fitted yet.")
        dts = pd.to_datetime(dates)
        t_days = (dts - self.base_date).dt.total_seconds() / (24 * 3600.0)
        t_norm = (t_days / 365.25).values

        # Trend component
        trend_coef = self.regressor.coef_[0]
        trend = self.regressor.intercept_ + trend_coef * t_norm

        # Seasonality
        doy = dts.dt.dayofyear.values
        annual_seasonal = np.zeros(len(dates))
        idx = 1
        for n in range(1, self.fourier_order_year + 1):
            annual_seasonal += (
                self.regressor.coef_[idx] * np.cos(2 * np.pi * n * doy / 365.25)
                + self.regressor.coef_[idx + 1] * np.sin(2 * np.pi * n * doy / 365.25)
            )
            idx += 2

        return {
            "trend": trend,
            "seasonal_annual": annual_seasonal,
            "fitted_total": self.predict(dates)
        }

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            "regressor": self.regressor,
            "base_date": self.base_date,
            "fourier_order_year": self.fourier_order_year,
            "fourier_order_week": self.fourier_order_week
        }, filepath)

    def load(self, filepath: str):
        data = joblib.load(filepath)
        self.regressor = data["regressor"]
        self.base_date = data["base_date"]
        self.fourier_order_year = data["fourier_order_year"]
        self.fourier_order_week = data["fourier_order_week"]
        self.is_fitted = True
        return self
