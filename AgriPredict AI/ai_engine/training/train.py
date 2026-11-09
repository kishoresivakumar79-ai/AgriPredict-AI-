"""
Model Training & Chronological Validation Pipeline.
Trains XGBoost, LSTM, Prophet, and Random Forest models on historical agricultural data.
Evaluates out-of-time test performance and persists serialized artifacts.
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from ai_engine.preprocessing.clean_data import clean_agricultural_data
from ai_engine.feature_engineering.features import build_features, get_feature_columns
from ai_engine.models.xgboost_model import AgriXGBoostModel
from ai_engine.models.random_forest import AgriRandomForestModel
from ai_engine.models.lstm_model import AgriLSTMModel
from ai_engine.models.prophet_model import AgriProphetModel
from ai_engine.training.evaluate import calculate_metrics

def train_and_evaluate_models(
    horizon: int = 15,
    sample_size: int = 12000,
    models_dir: Optional[str] = None,
    reports_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes end-to-end model training, chronological split evaluation, and persistence.
    """
    if models_dir is None:
        models_dir = str(PROJECT_ROOT / "trained_models")
    if reports_dir is None:
        reports_dir = str(PROJECT_ROOT / "reports")
    clean_path = str(PROJECT_ROOT / "datasets" / "processed" / "agricultural_market_clean.csv")
    if not os.path.exists(clean_path):
        clean_agricultural_data()

    print("Loading cleaned dataset...")
    df_clean = pd.read_csv(clean_path)

    print("Building features and lag structures...")
    df_feat = build_features(df_clean, horizons=[7, 15, 30])
    
    target_col = f"target_price_{horizon}d"
    df_feat = df_feat.dropna(subset=[target_col]).reset_index(drop=True)

    # Optional subsample for fast training while maintaining time order
    if len(df_feat) > sample_size:
        # Sample evenly across dates
        step = max(1, len(df_feat) // sample_size)
        df_feat = df_feat.iloc[::step].reset_index(drop=True)

    feature_cols = [c for c in get_feature_columns() if c in df_feat.columns]

    # Chronological Train-Test Split (Strictly chronological: first 80% train, last 20% test)
    df_feat = df_feat.sort_values("date").reset_index(drop=True)
    split_idx = int(len(df_feat) * 0.80)
    
    train_df = df_feat.iloc[:split_idx].copy()
    test_df = df_feat.iloc[split_idx:].copy()

    split_date = test_df["date"].min()
    print(f"Chronological split at: {split_date}. Train: {len(train_df):,} rows, Test: {len(test_df):,} rows")

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    models_path = Path(models_dir)
    reports_path = Path(reports_dir)
    models_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)

    results = {}

    # 1. XGBoost / Gradient Boosting
    print("Training Model 1: Gradient Boosting / XGBoost...")
    xgb_model = AgriXGBoostModel(n_estimators=120, learning_rate=0.08, max_depth=6)
    xgb_model.fit(X_train, y_train, feature_names=feature_cols)
    xgb_preds = xgb_model.predict(X_test)
    xgb_metrics = calculate_metrics(y_test, xgb_preds)
    xgb_model.save(str(models_path / "xgboost_model.joblib"))
    results["XGBoost"] = xgb_metrics
    print(f"XGBoost Test Metrics -> MAE: ₹{xgb_metrics['mae']}, RMSE: ₹{xgb_metrics['rmse']}, MAPE: {xgb_metrics['mape']}%")

    # 2. Random Forest
    print("Training Model 2: Random Forest Regressor...")
    rf_model = AgriRandomForestModel(n_estimators=80, max_depth=12)
    rf_model.fit(X_train, y_train, feature_names=feature_cols)
    rf_preds = rf_model.predict(X_test)
    rf_metrics = calculate_metrics(y_test, rf_preds)
    rf_model.save(str(models_path / "random_forest_model.joblib"))
    results["RandomForest"] = rf_metrics
    print(f"Random Forest Test Metrics -> MAE: ₹{rf_metrics['mae']}, RMSE: ₹{rf_metrics['rmse']}, MAPE: {rf_metrics['mape']}%")

    # 3. LSTM / Sequential Neural Network
    print("Training Model 3: Sequential Deep Neural Network (LSTM Architecture)...")
    lstm_model = AgriLSTMModel(sequence_length=30, hidden_layers=(128, 64))
    lstm_model.fit(X_train, y_train, feature_names=feature_cols)
    lstm_preds = lstm_model.predict(X_test)
    lstm_metrics = calculate_metrics(y_test, lstm_preds)
    lstm_model.save(str(models_path / "lstm_model.joblib"))
    results["LSTM"] = lstm_metrics
    print(f"LSTM Test Metrics -> MAE: ₹{lstm_metrics['mae']}, RMSE: ₹{lstm_metrics['rmse']}, MAPE: {lstm_metrics['mape']}%")

    # 4. Prophet Decomposable GAM Model
    print("Training Model 4: Prophet Trend & Harmonic Seasonality Model...")
    prophet_model = AgriProphetModel(fourier_order_year=5, fourier_order_week=2)
    prophet_model.fit(train_df["date"], y_train, additional_features=train_df[["temp_avg_c", "rainfall_mm", "drought_index"]])
    prophet_preds = prophet_model.predict(test_df["date"], additional_features=test_df[["temp_avg_c", "rainfall_mm", "drought_index"]])
    prophet_metrics = calculate_metrics(y_test, prophet_preds)
    prophet_model.save(str(models_path / "prophet_model.joblib"))
    results["Prophet"] = prophet_metrics
    print(f"Prophet Test Metrics -> MAE: ₹{prophet_metrics['mae']}, RMSE: ₹{prophet_metrics['rmse']}, MAPE: {prophet_metrics['mape']}%")

    # Determine Best Model (lowest MAE)
    best_model_name = min(results.keys(), key=lambda k: results[k]["mae"])
    print(f"\nChampion Model Selected: {best_model_name} with lowest MAE of ₹{results[best_model_name]['mae']}")

    # Save summary reports
    metrics_file = reports_path / "model_evaluation_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump({
            "split_date": split_date,
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "target_horizon_days": horizon,
            "models": results,
            "champion_model": best_model_name,
            "feature_importance_top10": list(rf_model.get_feature_importances().items())[:10]
        }, f, indent=2)

    comp_df = pd.DataFrame(results).T.reset_index().rename(columns={"index": "Model"})
    comp_df.to_csv(reports_path / "model_comparison.csv", index=False)
    print(f"Evaluation report persisted to {metrics_file}")

    return {
        "results": results,
        "champion_model": best_model_name,
        "split_date": split_date
    }

if __name__ == "__main__":
    train_and_evaluate_models()
