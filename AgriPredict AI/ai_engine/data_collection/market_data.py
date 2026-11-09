"""
Agricultural Market Price and Arrivals Data Collection Module.
Modeled after Agmarknet (Agricultural Marketing Information Network, Government of India)
and e-NAM (National Agriculture Market) records.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, List

from ai_engine.data_collection.weather_data import generate_historical_weather

def generate_agricultural_dataset(
    start_date: str = "2023-01-01",
    end_date: str = "2026-11-09",
    output_dir: Optional[str] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates rich, realistic daily agricultural market dataset
    with integrated weather, arrivals, demand index, and prices.
    """
    if output_dir is None:
        output_dir = str(PROJECT_ROOT / "datasets" / "raw")
    sample_dir = str(PROJECT_ROOT / "datasets" / "sample")
    
    np.random.seed(seed)
    weather_df = generate_historical_weather(start_date=start_date, end_date=end_date, seed=seed)

    
    crops_profile = {
        "Tomato": {
            "base_price": 1800.0,
            "price_volatility": 0.28,
            "base_arrivals_tonnes": 120.0,
            "shelf_life_category": "Perishable",
            # Seasonal peak: July-August (monsoon crop loss) and secondary in Nov
            "peak_months": [7, 8, 11],
            "glut_months": [1, 2, 3],
            "rain_damage_sensitivity": 0.45,
            "temp_stress_sensitivity": 0.25,
        },
        "Onion": {
            "base_price": 2200.0,
            "price_volatility": 0.22,
            "base_arrivals_tonnes": 160.0,
            "shelf_life_category": "Semi-Perishable",
            # Seasonal peak: Oct-Nov (pre-Kharif arrival lag)
            "peak_months": [9, 10, 11],
            "glut_months": [4, 5],
            "rain_damage_sensitivity": 0.35,
            "temp_stress_sensitivity": 0.15,
        },
        "Potato": {
            "base_price": 1650.0,
            "price_volatility": 0.15,
            "base_arrivals_tonnes": 200.0,
            "shelf_life_category": "Storable",
            # Seasonal peak: Sept-Nov (cold storage stocks winding down)
            "peak_months": [9, 10, 11],
            "glut_months": [2, 3, 4],
            "rain_damage_sensitivity": 0.12,
            "temp_stress_sensitivity": 0.10,
        },
        "Rice": {
            "base_price": 3200.0,
            "price_volatility": 0.08,
            "base_arrivals_tonnes": 280.0,
            "shelf_life_category": "Durable",
            "peak_months": [8, 9],
            "glut_months": [11, 12, 1],
            "rain_damage_sensitivity": 0.08,
            "temp_stress_sensitivity": 0.05,
        },
        "Maize": {
            "base_price": 2100.0,
            "price_volatility": 0.10,
            "base_arrivals_tonnes": 190.0,
            "shelf_life_category": "Durable",
            "peak_months": [6, 7],
            "glut_months": [10, 11, 12],
            "rain_damage_sensitivity": 0.10,
            "temp_stress_sensitivity": 0.08,
        }
    }

    # Mandi price multipliers (Coimbatore is consumption hub -> higher price; Salem/Erode closer to farm gate)
    market_premiums = {
        "Salem": {"price_mult": 0.96, "arrivals_mult": 1.05, "state": "Tamil Nadu", "district": "Salem"},
        "Erode": {"price_mult": 0.98, "arrivals_mult": 1.15, "state": "Tamil Nadu", "district": "Erode"},
        "Coimbatore": {"price_mult": 1.12, "arrivals_mult": 1.40, "state": "Tamil Nadu", "district": "Coimbatore"},
        "Namakkal": {"price_mult": 0.94, "arrivals_mult": 0.85, "state": "Tamil Nadu", "district": "Namakkal"},
        "Dindigul": {"price_mult": 0.95, "arrivals_mult": 0.90, "state": "Tamil Nadu", "district": "Dindigul"},
        "Nashik": {"price_mult": 0.92, "arrivals_mult": 2.20, "state": "Maharashtra", "district": "Nashik"},
        "Pune": {"price_mult": 1.10, "arrivals_mult": 1.60, "state": "Maharashtra", "district": "Pune"},
    }

    records = []
    weather_dict = weather_df.set_index(["market", "date"]).to_dict("index")

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    
    for dt in dates:
        dt_str = dt.strftime("%Y-%m-%d")
        month = dt.month
        day_of_week = dt.dayofweek # 6 is Sunday (usually lower market volume)
        doy = dt.dayofyear

        # Multi-year macro inflation drift (approx 4.5% annual agricultural cost escalation)
        year_fraction = (dt.year - 2023) + (doy / 365.25)
        inflation_factor = 1.0 + 0.045 * year_fraction

        for crop_name, cp in crops_profile.items():
            base_p = cp["base_price"] * inflation_factor
            vol = cp["price_volatility"]
            base_arr = cp["base_arrivals_tonnes"]

            # Seasonality multiplier
            if month in cp["peak_months"]:
                season_price_mult = 1.25 + 0.08 * np.sin(doy / 30)
                season_arr_mult = 0.72
            elif month in cp["glut_months"]:
                season_price_mult = 0.82 - 0.05 * np.cos(doy / 30)
                season_arr_mult = 1.38
            else:
                season_price_mult = 1.0 + 0.04 * np.sin(doy / 50)
                season_arr_mult = 1.0

            # Festival demand shocks (Diwali in Oct/Nov, Pongal in Jan)
            festival_demand_boost = 1.0
            if (month == 1 and dt.day in range(10, 18)) or (month in [10, 11] and dt.day in range(20, 31)):
                festival_demand_boost = 1.22

            for mkt_name, mkt_info in market_premiums.items():
                w_info = weather_dict.get((mkt_name, dt_str), {
                    "temp_avg_c": 28.0,
                    "rainfall_mm": 0.0,
                    "humidity_pct": 60.0,
                    "drought_index": 0.0,
                    "rain_14d_sum": 10.0
                })

                rain_val = w_info["rainfall_mm"]
                temp_val = w_info["temp_avg_c"]
                rain_14d = w_info["rain_14d_sum"]
                drought_idx = w_info["drought_index"]

                # Weather shock to supply
                weather_supply_impact = 1.0
                if rain_14d > 120.0 and cp["rain_damage_sensitivity"] > 0.2:
                    # Waterlogging damage -> reduced arrivals -> higher prices
                    damage_factor = (rain_14d - 120.0) / 100.0 * cp["rain_damage_sensitivity"]
                    weather_supply_impact = max(0.45, 1.0 - damage_factor)
                elif drought_idx > 1.2:
                    # Drought reduces yield
                    weather_supply_impact = max(0.65, 1.0 - (drought_idx - 1.2) * 0.15)

                # Day of week arrival adjustment (Sunday ~30% volume)
                dow_mult = 0.35 if day_of_week == 6 else (1.15 if day_of_week == 0 else 1.0)

                arrivals = (
                    base_arr 
                    * mkt_info["arrivals_mult"] 
                    * season_arr_mult 
                    * weather_supply_impact 
                    * dow_mult 
                    * np.random.uniform(0.85, 1.15)
                )
                arrivals = round(max(5.0, arrivals), 1)

                # Estimated market demand index (base 100.0)
                demand_index = round(
                    100.0 * festival_demand_boost * mkt_info["price_mult"] * np.random.uniform(0.95, 1.05),
                    2
                )

                # Price determination based on economic equilibrium:
                # Inversely related to arrivals, directly related to demand, with persistence
                supply_ratio = (arrivals / (base_arr * mkt_info["arrivals_mult"] * dow_mult + 1e-4))
                price_adj = (demand_index / 100.0) / (supply_ratio ** 0.5)

                modal_price = (
                    base_p 
                    * mkt_info["price_mult"] 
                    * season_price_mult 
                    * price_adj 
                    * (1.0 + np.random.normal(0, vol * 0.35))
                )
                modal_price = round(max(350.0, modal_price), 0)

                # Min & Max spread based on grading & quality variance
                spread_pct = np.random.uniform(0.06, 0.14)
                min_price = round(modal_price * (1.0 - spread_pct), 0)
                max_price = round(modal_price * (1.0 + spread_pct * 1.1), 0)

                records.append({
                    "date": dt_str,
                    "crop": crop_name,
                    "market": mkt_name,
                    "state": mkt_info["state"],
                    "district": mkt_info["district"],
                    "category": cp["shelf_life_category"],
                    "modal_price": float(modal_price),
                    "min_price": float(min_price),
                    "max_price": float(max_price),
                    "arrivals_tonnes": float(arrivals),
                    "demand_index": float(demand_index),
                    "temp_avg_c": float(temp_val),
                    "rainfall_mm": float(rain_val),
                    "humidity_pct": float(w_info["humidity_pct"]),
                    "drought_index": float(drought_idx),
                    "rain_14d_sum": float(rain_14d)
                })

    df = pd.DataFrame(records)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(sample_dir, exist_ok=True)
    
    csv_path = os.path.join(output_dir, "agricultural_market_data.csv")
    sample_path = os.path.join(sample_dir, "market_data_sample.csv")
    
    df.to_csv(csv_path, index=False)
    # Write a smaller representative sample (latest 500 rows)
    df.tail(500).to_csv(sample_path, index=False)
    
    print(f"Dataset generated: {len(df):,} records saved to {csv_path}")
    return df

if __name__ == "__main__":
    generate_agricultural_dataset()
