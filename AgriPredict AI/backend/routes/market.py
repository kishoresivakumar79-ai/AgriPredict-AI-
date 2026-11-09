"""
FastAPI Routes for Agricultural Mandi Market Analysis & Inter-Mandi Arbitrage.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict
from backend.services.price_service import PriceService
from recommendation.market_recommendation import MarketComparisonEngine

router = APIRouter(prefix="/api/market", tags=["Market Analysis"])
price_service = PriceService()
comparison_engine = MarketComparisonEngine()

@router.get("/history")
def get_historical_market_data(
    crop: str = "Tomato",
    market: str = "Salem",
    days: int = 90
):
    """Returns historical price, arrival volumes, and weather conditions."""
    return price_service.get_historical_trends(crop=crop, market=market, days=days)

@router.get("/compare")
def compare_mandi_prices(
    crop: str = "Tomato",
    origin_market: str = "Salem",
    quantity_quintals: float = 100.0,
    diesel_cost_multiplier: float = 1.0
):
    """Compares price spreads, logistics costs, and net revenue across markets."""
    latest_prices = price_service.get_all_market_prices_latest(crop=crop)
    return comparison_engine.compare_markets(
        crop=crop,
        origin_market=origin_market,
        quantity_quintals=quantity_quintals,
        market_prices=latest_prices,
        diesel_cost_multiplier=diesel_cost_multiplier
    )

@router.get("/list")
def list_markets_and_crops():
    """Returns available mandis and supported commodities."""
    return {
        "crops": ["Tomato", "Onion", "Potato", "Rice", "Maize"],
        "markets": list(comparison_engine.markets_info.keys()),
        "market_details": comparison_engine.markets_info
    }
