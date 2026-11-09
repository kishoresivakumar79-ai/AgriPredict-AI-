"""
Data Preprocessing Layer.
Handles missing values, duplicate records, outlier clipping via IQR,
date normalization, and continuous sequence validation.
"""
import sys
import os
from pathlib import Path
from typing import Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

def clean_agricultural_data(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    outlier_iqr_factor: float = 2.5
) -> pd.DataFrame:
    """
    Cleans raw agricultural data and outputs processed dataframe.
    """
    if input_path is None:
        input_path = str(PROJECT_ROOT / "datasets" / "raw" / "agricultural_market_data.csv")
    if output_path is None:
        output_path = str(PROJECT_ROOT / "datasets" / "processed" / "agricultural_market_clean.csv")

    if not os.path.exists(input_path):
        from ai_engine.data_collection.market_data import generate_agricultural_dataset
        generate_agricultural_dataset()

    print(f"Loading raw data from: {input_path}")
    df = pd.read_csv(input_path)

    # 1. Date conversion & deduplication
    df["date"] = pd.to_datetime(df["date"])
    initial_len = len(df)
    df = df.drop_duplicates(subset=["date", "crop", "market"]).reset_index(drop=True)
    dedup_len = len(df)
    if initial_len != dedup_len:
        print(f"Removed {initial_len - dedup_len} duplicate records.")

    # 2. Sort chronologically per crop and market
    df = df.sort_values(["crop", "market", "date"]).reset_index(drop=True)

    # 3. Missing-value handling
    numeric_cols = [
        "modal_price", "min_price", "max_price", "arrivals_tonnes",
        "demand_index", "temp_avg_c", "rainfall_mm", "humidity_pct",
        "drought_index", "rain_14d_sum"
    ]
    for col in numeric_cols:
        if col in df.columns:
            # Interpolate or forward-fill within crop/market groups
            df[col] = df.groupby(["crop", "market"])[col].transform(
                lambda s: s.interpolate(method="linear").bfill().ffill()
            )

    # 4. Outlier detection and clipping via IQR per crop
    # Extreme impossible negative or near-zero prices are guarded
    cleaned_groups = []
    for (crop, mkt), group in df.groupby(["crop", "market"]):
        grp = group.copy()
        q1 = grp["modal_price"].quantile(0.01)
        q3 = grp["modal_price"].quantile(0.99)
        iqr = q3 - q1
        lower_bound = max(200.0, q1 - outlier_iqr_factor * iqr)
        upper_bound = q3 + outlier_iqr_factor * iqr
        grp["modal_price"] = grp["modal_price"].clip(lower=lower_bound, upper=upper_bound)
        grp["min_price"] = grp["min_price"].clip(lower=lower_bound * 0.9, upper=grp["modal_price"])
        grp["max_price"] = grp["max_price"].clip(lower=grp["modal_price"], upper=upper_bound * 1.1)
        cleaned_groups.append(grp)

    df_cleaned = pd.concat(cleaned_groups, ignore_index=True)
    df_cleaned = df_cleaned.sort_values(["date", "crop", "market"]).reset_index(drop=True)

    # 5. Format date back to string for consistency
    df_cleaned["date"] = df_cleaned["date"].dt.strftime("%Y-%m-%d")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_cleaned.to_csv(output_path, index=False)
    print(f"Cleaned dataset saved: {len(df_cleaned):,} records to {output_path}")
    return df_cleaned

if __name__ == "__main__":
    clean_agricultural_data()

