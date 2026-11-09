"""
FastAPI Routes for Weather Impact Analysis.
"""
from fastapi import APIRouter, Query
from simulation.weather_impact import WeatherImpactSimulator
from backend.services.price_service import PriceService

router = APIRouter(prefix="/api/weather", tags=["Weather Analysis"])
weather_sim = WeatherImpactSimulator()
price_service = PriceService()

@router.get("/impact")
def analyze_weather_impact(
    crop: str = Query("Tomato"),
    market: str = Query("Salem"),
    rainfall_anomaly_pct: float = Query(0.0),
    temp_anomaly_c: float = Query(0.0),
    drought_severity: float = Query(0.0),
    flood_severity: float = Query(0.0)
):
    """Simulates production loss and price surge driven by weather events."""
    current_p = price_service.get_price_forecast(crop, market)["current_price"]
    return weather_sim.simulate_weather_shock(
        crop=crop,
        base_price=current_p,
        rainfall_anomaly_pct=rainfall_anomaly_pct,
        temp_anomaly_c=temp_anomaly_c,
        drought_severity=drought_severity,
        flood_severity=flood_severity
    )

