"""
Weather Data Collection and Synthesis Module.
Simulates and collects meteorological data (Rainfall, Temp, Humidity, Drought/Flood conditions)
modeled after NASA POWER and IMD meteorological stations for Indian agricultural hubs.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict

def generate_historical_weather(
    start_date: str = "2023-01-01",
    end_date: str = "2026-11-09",
    markets: Optional[Dict] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates realistic daily weather records per market.
    Captures Indian monsoon dynamics (Southwest & Northeast monsoon),
    temperature cycles, heatwaves, and extreme precipitation anomalies.
    """
    np.random.seed(seed)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    records = []

    if markets is None:
        markets = {
            "Salem": {"lat": 11.66, "base_temp": 28.5, "annual_rain": 950},
            "Erode": {"lat": 11.34, "base_temp": 29.0, "annual_rain": 820},
            "Coimbatore": {"lat": 11.01, "base_temp": 26.5, "annual_rain": 720},
            "Namakkal": {"lat": 11.21, "base_temp": 28.8, "annual_rain": 860},
            "Dindigul": {"lat": 10.36, "base_temp": 28.0, "annual_rain": 890},
            "Nashik": {"lat": 19.99, "base_temp": 25.5, "annual_rain": 980},
            "Pune": {"lat": 18.52, "base_temp": 26.0, "annual_rain": 900},
        }

    for market_name, m_info in markets.items():
        base_t = m_info.get("base_temp", 28.0)
        lat = m_info.get("lat", 12.0)
        is_tn = lat < 14.0  # Tamil Nadu gets high rain in Northeast Monsoon (Oct-Dec)

        for dt in date_range:
            doy = dt.dayofyear
            # Temperature seasonal variation (Peaking in April-May ~DOY 100-140)
            temp_season = 5.0 * np.sin(2 * np.pi * (doy - 45) / 365)
            daily_temp = base_t + temp_season + np.random.normal(0, 1.2)
            temp_max = daily_temp + np.random.uniform(3.5, 7.0)
            temp_min = daily_temp - np.random.uniform(3.5, 6.0)

            # Rainfall model
            rainfall = 0.0
            month = dt.month

            # Monsoon probabilities
            if is_tn:
                # Tamil Nadu: high rain Oct, Nov, Dec (Northeast monsoon), moderate in SW monsoon (Jul-Aug)
                if month in [10, 11, 12]:
                    p_rain = 0.42
                    rain_scale = 16.0
                elif month in [6, 7, 8, 9]:
                    p_rain = 0.28
                    rain_scale = 9.0
                else:
                    p_rain = 0.08
                    rain_scale = 3.0
            else:
                # Maharashtra (Nashik/Pune): High rain June-Sept (Southwest monsoon)
                if month in [6, 7, 8, 9]:
                    p_rain = 0.52
                    rain_scale = 22.0
                else:
                    p_rain = 0.05
                    rain_scale = 2.0

            if np.random.rand() < p_rain:
                rainfall = np.random.exponential(scale=rain_scale)
                # Occasional extreme cloudburst / heavy rain event
                if np.random.rand() < 0.03:
                    rainfall += np.random.uniform(40.0, 95.0)

            rainfall = round(max(0.0, rainfall), 1)

            # Humidity correlates positively with rainfall & seasonality
            base_humidity = 55.0
            if rainfall > 10:
                humidity = np.clip(base_humidity + 25 + np.random.normal(0, 4), 60, 98)
            elif month in [3, 4, 5]:
                humidity = np.clip(base_humidity - 18 + np.random.normal(0, 5), 25, 60)
            else:
                humidity = np.clip(base_humidity + np.random.normal(0, 6), 35, 85)

            # Drought / Flood Index (-2.0 extreme drought, +2.0 flood)
            # Computed as rolling normalized moisture indicator
            records.append({
                "date": dt.strftime("%Y-%m-%d"),
                "market": market_name,
                "temp_avg_c": round(daily_temp, 2),
                "temp_max_c": round(temp_max, 2),
                "temp_min_c": round(temp_min, 2),
                "rainfall_mm": rainfall,
                "humidity_pct": round(humidity, 1)
            })

    df = pd.DataFrame(records)
    # Calculate 14-day cumulative rainfall and drought index
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["market", "date"]).reset_index(drop=True)
    df["rain_14d_sum"] = df.groupby("market")["rainfall_mm"].transform(lambda x: x.rolling(14, min_periods=1).sum())
    
    # Drought index heuristic: low 14d rain + high temp = drought
    mean_rain = df.groupby("market")["rain_14d_sum"].transform("mean")
    std_rain = df.groupby("market")["rain_14d_sum"].transform("std") + 1e-4
    df["moisture_anomaly"] = (df["rain_14d_sum"] - mean_rain) / std_rain
    df["drought_index"] = np.clip(-df["moisture_anomaly"], -3.0, 3.0).round(2)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df

