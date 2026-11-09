"""
FastAPI Routes for Crop Price Prediction & Model Metrics.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import json
from pathlib import Path

from backend.services.price_service import PriceService
from backend.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/prediction", tags=["Price Prediction"])
price_service = PriceService()

@router.get("/forecast")
def get_prediction_forecast(
    crop: str = Query("Tomato", description="Crop name"),
    market: str = Query("Salem", description="Mandi market"),
    horizon: int = Query(15, description="Forecast horizon in days (7, 15, 30)"),
    model: str = Query("Ensemble", description="ML model: Ensemble, XGBoost, RandomForest, LSTM, Prophet")
):
    """Generates predicted crop price and day-by-day trajectory."""
    try:
        return price_service.get_price_forecast(crop=crop, market=market, horizon_days=horizon, model_name=model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
def get_available_models():
    """Returns available machine learning architectures."""
    return {
        "models": [
            {"id": "Ensemble", "name": "AI Weighted Ensemble", "description": "Combines Gradient Boosting, Random Forest, LSTM, and Prophet"},
            {"id": "XGBoost", "name": "XGBoost / Gradient Boosting", "description": "High non-linear weather-market arrival regression"},
            {"id": "RandomForest", "name": "Random Forest Regressor", "description": "Multi-tree bagging with empirical uncertainty quantification"},
            {"id": "LSTM", "name": "LSTM / Sequential Deep NN", "description": "Recurrent time-series sliding window architecture"},
            {"id": "Prophet", "name": "Prophet GAM Decomposer", "description": "Harmonic Fourier seasonality and macro trend forecasting"}
        ],
        "champion_model": price_service.predictor.champion_model
    }

@router.get("/metrics")
def get_evaluation_metrics():
    """Returns out-of-time chronological validation metrics across all models."""
    metrics_path = Path(__file__).resolve().parent.parent.parent / "reports" / "model_evaluation_metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {"message": "Metrics not found. Run train.py to evaluate models."}

