"""
Recommendation Service Layer.
Integrates Decision Engine, Storage Simulator, and Market Comparison.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.price_service import PriceService
from simulation.storage_simulator import StorageSimulator
from recommendation.market_recommendation import MarketComparisonEngine
from recommendation.decision_engine import AgriDecisionEngine
from simulation.weather_impact import WeatherImpactSimulator

class RecommendationService:
    def __init__(self):
        self.price_service = PriceService()
        self.storage_sim = StorageSimulator()
        self.market_comp = MarketComparisonEngine()
        self.decision_engine = AgriDecisionEngine()
        self.weather_sim = WeatherImpactSimulator()

    def get_full_farmer_advisory(
        self,
        crop: str,
        current_market: str,
        quantity_quintals: float = 100.0,
        horizon_days: int = 15,
        use_cold_storage: bool = True
    ) -> Dict[str, Any]:
        # 1. Price Prediction
        forecast = self.price_service.get_price_forecast(crop, current_market, horizon_days=horizon_days)
        curr_p = forecast["current_price"]
        pred_p = forecast["predicted_price"]

        # Forecasts for 7, 15, 30 days
        f7 = self.price_service.get_price_forecast(crop, current_market, horizon_days=7)["predicted_price"]
        f15 = pred_p
        f30 = self.price_service.get_price_forecast(crop, current_market, horizon_days=30)["predicted_price"]

        # 2. Storage simulation
        storage_res = self.storage_sim.simulate_strategies(
            crop=crop,
            quantity_quintals=quantity_quintals,
            current_price=curr_p,
            price_7d=f7,
            price_15d=f15,
            price_30d=f30,
            use_cold_storage=use_cold_storage
        )

        # 3. Market price comparison
        all_prices = self.price_service.get_all_market_prices_latest(crop)
        market_res = self.market_comp.compare_markets(
            crop=crop,
            origin_market=current_market,
            quantity_quintals=quantity_quintals,
            market_prices=all_prices
        )

        # 4. Weather baseline
        weather_res = self.weather_sim.simulate_weather_shock(crop=crop, base_price=curr_p)

        # 5. Composite Decision
        decision = self.decision_engine.generate_recommendation(
            crop=crop,
            current_market=current_market,
            current_price=curr_p,
            predicted_price_15d=pred_p,
            storage_analysis=storage_res,
            market_comparison=market_res,
            weather_analysis=weather_res,
            quantity_quintals=quantity_quintals
        )

        return {
            "forecast": forecast,
            "storage_analysis": storage_res,
            "market_comparison": market_res,
            "decision": decision
        }

