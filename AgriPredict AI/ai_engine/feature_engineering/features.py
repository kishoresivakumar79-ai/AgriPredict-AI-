"""
Feature Engineering Layer.
Generates lagged prices, rolling averages, volatility, weather impact features,
temporal cyclical encodings, and agricultural calendar factors.
"""
import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

def build_features(
    df: pd.DataFrame,
    horizons: List[int] = [7, 15, 30]
) -> pd.DataFrame:
    """
    Constructs ML features for price forecasting.
    Expects clean dataframe sorted by date within crop and market.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["crop", "market", "date"]).reset_index(drop=True)

    # 1. Temporal & Cyclical Features
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_year"] = df["date"].dt.dayofyear
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Cyclical sine/cosine encoding for seasonality
    df["sin_doy"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)

    # Agricultural seasons in India:
    # Kharif: July to October (Months 7, 8, 9, 10)
    # Rabi: November to March (Months 11, 12, 1, 2, 3)
    # Zaid / Summer: April to June (Months 4, 5, 6)
    def get_season(m):
        if m in [7, 8, 9, 10]:
            return "Kharif"
        elif m in [11, 12, 1, 2, 3]:
            return "Rabi"
        else:
            return "Zaid"
    df["season"] = df["month"].apply(get_season)

    # 2. Lag Features per Crop & Market Group
    group = df.groupby(["crop", "market"])

    # Price Lags
    df["price_lag_1"] = group["modal_price"].shift(1)
    df["price_lag_2"] = group["modal_price"].shift(2)
    df["price_lag_3"] = group["modal_price"].shift(3)
    df["price_lag_7"] = group["modal_price"].shift(7)
    df["price_lag_14"] = group["modal_price"].shift(14)
    df["price_lag_30"] = group["modal_price"].shift(30)

    # Rolling Price Averages & Volatility
    df["price_roll_mean_7"] = group["modal_price"].transform(lambda x: x.shift(1).rolling(7, min_periods=3).mean())
    df["price_roll_mean_30"] = group["modal_price"].transform(lambda x: x.shift(1).rolling(30, min_periods=7).mean())
    df["price_roll_std_7"] = group["modal_price"].transform(lambda x: x.shift(1).rolling(7, min_periods=3).std().fillna(0))
    df["price_roll_std_30"] = group["modal_price"].transform(lambda x: x.shift(1).rolling(30, min_periods=7).std().fillna(0))

    # Rolling Momentum & Rate of Change
    df["price_momentum_7"] = (df["price_lag_1"] - df["price_lag_7"]) / (df["price_lag_7"] + 1e-4)

    # Arrivals Lags & Rolling Volumes
    df["arrivals_lag_1"] = group["arrivals_tonnes"].shift(1)
    df["arrivals_lag_7"] = group["arrivals_tonnes"].shift(7)
    df["arrivals_roll_mean_7"] = group["arrivals_tonnes"].transform(lambda x: x.shift(1).rolling(7, min_periods=3).mean())
    df["arrivals_roll_mean_30"] = group["arrivals_tonnes"].transform(lambda x: x.shift(1).rolling(30, min_periods=7).mean())

    # Supply-Demand Ratio Feature
    df["supply_demand_ratio"] = df["arrivals_lag_1"] / (df["demand_index"] + 1e-4)

    # Weather Cumulative & Anomaly Features
    df["rain_roll_mean_7"] = group["rainfall_mm"].transform(lambda x: x.rolling(7, min_periods=1).mean())
    df["temp_roll_mean_7"] = group["temp_avg_c"].transform(lambda x: x.rolling(7, min_periods=1).mean())

    # 3. Future Price Targets for horizons (7, 15, 30 days ahead)
    for h in horizons:
        df[f"target_price_{h}d"] = group["modal_price"].shift(-h)

    # Target default (15-day ahead or 1-day)
    df["target_price"] = df.get("target_price_15d", group["modal_price"].shift(-1))

    # Drop early warmup rows with NaNs from 30-day lag
    df = df.dropna(subset=["price_lag_30", "price_roll_mean_30"]).reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df

def get_feature_columns() -> List[str]:
    """Returns the standard feature list used for machine learning."""
    return [
        "price_lag_1", "price_lag_2", "price_lag_3", "price_lag_7", "price_lag_14", "price_lag_30",
        "price_roll_mean_7", "price_roll_mean_30", "price_roll_std_7", "price_roll_std_30",
        "price_momentum_7",
        "arrivals_lag_1", "arrivals_lag_7", "arrivals_roll_mean_7", "arrivals_roll_mean_30",
        "supply_demand_ratio",
        "temp_avg_c", "temp_roll_mean_7",
        "rainfall_mm", "rain_roll_mean_7", "rain_14d_sum",
        "humidity_pct", "drought_index",
        "sin_doy", "cos_doy", "sin_month", "cos_month", "day_of_week", "is_weekend"
    ]

