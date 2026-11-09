"""
Page: Weather Impact & Agricultural Vulnerability Analysis.
Simulates meteorological anomalies (excess rainfall, drought stress, heatwaves)
and traces causal propagation into production loss and price surges.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any

from frontend.components.charts import create_weather_impact_chart
from backend.services.price_service import PriceService
from simulation.weather_impact import WeatherImpactSimulator

def render_weather_analysis_page(settings: Dict[str, Any]):
    crop = settings["crop"]
    mandi = settings["mandi"]

    price_service = PriceService()
    weather_sim = WeatherImpactSimulator()

    st.markdown(f"## 🌦️ Weather Impact Analysis & Climate Risk")
    st.markdown(
        f"Analyze how rainfall variations, drought, and temperature anomalies influence "
        f"crop yields and drive wholesale market price volatility for **{crop}**."
    )

    # Historical Weather vs Price Chart
    hist_records = price_service.get_historical_trends(crop=crop, market=mandi, days=60)
    hist_df = pd.DataFrame(hist_records)
    if not hist_df.empty:
        fig = create_weather_impact_chart(hist_df)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🧪 Weather Scenario Stress Tester")
    st.write("Adjust meteorological deviation parameters to simulate shock impact on the current market price.")

    curr_p = float(hist_df["modal_price"].iloc[-1]) if not hist_df.empty else 1800.0

    c1, c2, c3 = st.columns(3)
    with c1:
        rain_anomaly = st.slider("Rainfall Anomaly (%)", min_value=-60.0, max_value=100.0, value=35.0, step=5.0, help="Negative indicates drought; positive indicates excess monsoon")
    with c2:
        temp_anomaly = st.slider("Temperature Anomaly (°C)", min_value=-2.0, max_value=6.0, value=1.5, step=0.5, help="Heatwave or thermal stress above historical average")
    with c3:
        flood_severity = st.slider("Waterlogging / Flood Severity", min_value=0.0, max_value=2.0, value=0.0, step=0.2, help="0: None, 1.0: Moderate waterlogging, 2.0: Severe flood")

    # Run weather shock simulation
    sim_res = weather_sim.simulate_weather_shock(
        crop=crop,
        base_price=curr_p,
        rainfall_anomaly_pct=rain_anomaly,
        temp_anomaly_c=temp_anomaly,
        flood_severity=flood_severity
    )

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Base Spot Price", f"₹{sim_res['base_price']:,.0f} / q")
    with m2:
        st.metric("Crop Yield Damage", f"{sim_res['yield_damage_pct']:.1f}%", delta=f"-{sim_res['yield_damage_pct']:.1f}% Yield", delta_color="inverse")
    with m3:
        st.metric("Arrival Supply Reduction", f"{sim_res['supply_contraction_pct']:.1f}%", delta=f"-{sim_res['supply_contraction_pct']:.1f}% Supply", delta_color="inverse")
    with m4:
        st.metric("Simulated Impact Price", f"₹{sim_res['simulated_price']:,.0f} / q", delta=f"+{sim_res['price_increase_pct']:.1f}%")

    st.markdown("#### 🔗 Causal Propagation Chain")
    for step in sim_res["causal_chain"]:
        st.markdown(f"• `{step}`")

