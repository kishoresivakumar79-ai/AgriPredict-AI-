"""
Price Service Layer.
Connects business logic and predictors for FastAPI endpoints.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from ai_engine.prediction.predict import AgriPredictor

class PriceService:
    def __init__(self):
        self.predictor = AgriPredictor()

    def get_price_forecast(
        self,
        crop: str,
        market: str,
        horizon_days: int = 15,
        model_name: str = "Ensemble",
        custom_price: Optional[float] = None
    ) -> Dict[str, Any]:
        return self.predictor.predict_price(
            crop=crop,
            market=market,
            horizon_days=horizon_days,
            model_name=model_name,
            custom_current_price=custom_price
        )

    def get_historical_trends(
        self,
        crop: str,
        market: str,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        clean_path = PROJECT_ROOT / "datasets" / "processed" / "agricultural_market_clean.csv"
        df = pd.read_csv(clean_path)
        sub = df[(df["crop"] == crop) & (df["market"] == market)].sort_values("date").tail(days)
        return sub[["date", "modal_price", "min_price", "max_price", "arrivals_tonnes", "temp_avg_c", "rainfall_mm"]].to_dict(orient="records")

    def get_all_market_prices_latest(self, crop: str) -> Dict[str, float]:
        clean_path = PROJECT_ROOT / "datasets" / "processed" / "agricultural_market_clean.csv"
        df = pd.read_csv(clean_path)
        sub = df[df["crop"] == crop].sort_values("date")
        latest_date = sub["date"].max()
        latest = sub[sub["date"] == latest_date]
        return dict(zip(latest["market"], latest["modal_price"]))

