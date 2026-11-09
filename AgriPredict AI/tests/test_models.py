"""
Unit Tests for Machine Learning Models, Predictions, and Evaluation Metrics.
"""
import pytest
import sys
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.training.evaluate import calculate_metrics
from ai_engine.models.xgboost_model import AgriXGBoostModel
from ai_engine.models.random_forest import AgriRandomForestModel
from ai_engine.prediction.predict import AgriPredictor

def test_metrics_calculation():
    y_true = np.array([1000.0, 1500.0, 2000.0])
    y_pred = np.array([1050.0, 1450.0, 1950.0])
    metrics = calculate_metrics(y_true, y_pred)
    assert metrics["mae"] == 50.0
    assert metrics["rmse"] == 50.0
    assert metrics["mape"] > 0.0

def test_random_forest_confidence_prediction():
    X = pd.DataFrame({
        "f1": np.random.uniform(10, 50, 100),
        "f2": np.random.uniform(5, 25, 100)
    })
    y = X["f1"] * 2.0 + X["f2"] * 1.5 + np.random.normal(0, 1, 100)
    rf = AgriRandomForestModel(n_estimators=20, max_depth=5)
    rf.fit(X, y)

    X_test = X.iloc[:5]
    expected, opt, pes = rf.predict_with_confidence(X_test)
    assert len(expected) == 5
    assert np.all(opt >= expected)
    assert np.all(expected >= pes)

def test_agri_predictor_inference():
    predictor = AgriPredictor()
    pred_res = predictor.predict_price(
        crop="Tomato",
        market="Salem",
        horizon_days=15,
        model_name="Ensemble"
    )
    assert "current_price" in pred_res
    assert "predicted_price" in pred_res
    assert "optimistic_price" in pred_res
    assert "pessimistic_price" in pred_res
    assert pred_res["optimistic_price"] >= pred_res["predicted_price"]
    assert pred_res["predicted_price"] >= pred_res["pessimistic_price"]
    assert len(pred_res["forecast_curve"]) == 15

