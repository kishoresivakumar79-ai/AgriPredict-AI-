"""
Unit Tests for FastAPI Backend Route Handlers and Endpoints.
Directly tests handler functions to ensure high performance and reliable schema validation.
"""
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import root, health_check
from backend.routes.prediction import get_prediction_forecast, get_available_models
from backend.routes.market import compare_mandi_prices, list_markets_and_crops
from backend.routes.simulation import (
    simulate_supply_demand,
    simulate_storage_decision,
    calculate_farmer_profit,
    simulate_what_if_scenario,
    ask_farmer_assistant
)

def test_api_root():
    res = root()
    assert res["status"] == "Online"
    assert "AgriPredict" in res["app"]

def test_health_check():
    res = health_check()
    assert res["status"] == "healthy"

def test_prediction_forecast_route():
    data = get_prediction_forecast(crop="Tomato", market="Salem", horizon=15, model="Ensemble")
    assert data["crop"] == "Tomato"
    assert data["market"] == "Salem"
    assert "predicted_price" in data
    assert "forecast_curve" in data

def test_available_models_route():
    data = get_available_models()
    assert len(data["models"]) >= 4
    assert "champion_model" in data

def test_market_compare_route():
    data = compare_mandi_prices(crop="Tomato", origin_market="Salem", quantity_quintals=100.0)
    assert "best_market" in data
    assert len(data["comparisons"]) > 0

def test_supply_demand_route():
    data = simulate_supply_demand(crop="Tomato", base_price=1800.0, base_supply=120.0, new_supply=160.0)
    assert data["new_simulated_price"] < 1800.0
    assert data["price_change_pct"] < 0

def test_farmer_profit_route():
    data = calculate_farmer_profit(crop="Tomato", quantity_quintals=100.0, selling_price=2000.0)
    assert data["gross_revenue"] == 200000.0
    assert data["net_profit"] > 0

def test_what_if_route():
    data = simulate_what_if_scenario(crop="Tomato", base_price=1800.0, rainfall_anomaly_pct=40.0)
    assert "simulated_mandi_price" in data
    assert len(data["insights"]) > 0

def test_assistant_route():
    data = ask_farmer_assistant({"question": "What is the tomato price in Salem?"})
    assert "answer_markdown" in data
    assert data["detected_crop"] == "Tomato"
