"""
Weather Impact Analysis & Crop Damage Simulation.
Models causal chains from rainfall deviations, drought, heatwaves, and floods
to agricultural yields, market arrival contractions, and equilibrium price surges.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class WeatherImpactSimulator:
    """
    Simulates weather-induced shocks on crop production and mandi prices.
    """
    # Sensitivity of crops to weather phenomena
    VULNERABILITY_INDEX = {
        "Tomato": {"excess_rain": 0.85, "drought": 0.65, "heatwave": 0.50, "shelf_life": "Very Low"},
        "Onion": {"excess_rain": 0.75, "drought": 0.50, "heatwave": 0.40, "shelf_life": "Medium"},
        "Potato": {"excess_rain": 0.60, "drought": 0.45, "heatwave": 0.70, "shelf_life": "High"},
        "Rice": {"excess_rain": 0.30, "drought": 0.85, "heatwave": 0.35, "shelf_life": "Very High"},
        "Maize": {"excess_rain": 0.40, "drought": 0.70, "heatwave": 0.45, "shelf_life": "Very High"}
    }

    def simulate_weather_shock(
        self,
        crop: str,
        base_price: float,
        rainfall_anomaly_pct: float = 0.0,
        temp_anomaly_c: float = 0.0,
        drought_severity: float = 0.0,
        flood_severity: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculates production loss, market arrival drop, and simulated price hike.
        """
        vuln = self.VULNERABILITY_INDEX.get(crop, {"excess_rain": 0.5, "drought": 0.5, "heatwave": 0.5})

        # Calculate harvest damage percentage
        damage_pct = 0.0
        causal_events = []

        if rainfall_anomaly_pct > 25.0 or flood_severity > 0.0:
            rain_loss = (rainfall_anomaly_pct / 100.0) * vuln["excess_rain"] * 35.0
            flood_loss = flood_severity * vuln["excess_rain"] * 40.0
            damage_pct += rain_loss + flood_loss
            causal_events.append(f"Excess monsoon / flood damage ({rainfall_anomaly_pct:+.1f}% rainfall)")

        if rainfall_anomaly_pct < -25.0 or drought_severity > 0.0:
            dry_loss = (abs(rainfall_anomaly_pct) / 100.0) * vuln["drought"] * 30.0
            drought_loss = drought_severity * vuln["drought"] * 35.0
            damage_pct += dry_loss + drought_loss
            causal_events.append(f"Moisture deficit / drought stress (severity: {drought_severity:.1f})")

        if temp_anomaly_c > 2.0:
            heat_loss = temp_anomaly_c * vuln["heatwave"] * 6.0
            damage_pct += heat_loss
            causal_events.append(f"Thermal stress / heatwave (+{temp_anomaly_c:.1f}°C anomaly)")

        # Crop harvest damage bounded between 0% and 75%
        damage_pct = min(75.0, max(0.0, damage_pct))

        # Supply arrival reduction
        arrival_reduction_pct = damage_pct * 0.95
        remaining_supply_ratio = max(0.25, 1.0 - (arrival_reduction_pct / 100.0))

        # Price multiplier using inverse elasticity
        price_elasticity = 0.60
        price_multiplier = (1.0 / remaining_supply_ratio) ** price_elasticity
        simulated_price = round(base_price * price_multiplier, 0)
        price_increase_pct = round(((simulated_price - base_price) / base_price) * 100.0, 2)

        # Causal explanation chain
        chain = [
            f"1. Extreme weather event detected: {', '.join(causal_events) if causal_events else 'Normal weather conditions'}",
            f"2. Agricultural crop yield reduced by ~{damage_pct:.1f}% across regional catchment",
            f"3. Mandi daily arrivals contract by ~{arrival_reduction_pct:.1f}% as supply tightens",
            f"4. Market demand exceeds available supply ({remaining_supply_ratio*100:.1f}% of normal)",
            f"5. Modal market price shifts from ₹{base_price:.0f} to ₹{simulated_price:.0f} (+{price_increase_pct:.1f}%)"
        ]

        return {
            "crop": crop,
            "base_price": round(base_price, 0),
            "simulated_price": round(simulated_price, 0),
            "price_increase_pct": price_increase_pct,
            "yield_damage_pct": round(damage_pct, 1),
            "supply_contraction_pct": round(arrival_reduction_pct, 1),
            "causal_chain": chain,
            "weather_risk_level": "High" if damage_pct > 25.0 else ("Moderate" if damage_pct > 10.0 else "Low")
        }

