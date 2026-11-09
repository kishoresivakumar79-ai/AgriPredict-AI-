"""
Page: Supply & Demand Economic Simulator.
Simulates non-linear market equilibrium shifts using calibrated price elasticity:
P_new = P_base * ((D_new / D_base) / (S_new / S_base)) ^ epsilon
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from typing import Dict, Any

from backend.services.price_service import PriceService
from simulation.supply_demand import SupplyDemandSimulator

def render_supply_demand_page(settings: Dict[str, Any]):
    crop = settings["crop"]
    mandi = settings["mandi"]

    price_service = PriceService()
    sd_sim = SupplyDemandSimulator()

    st.markdown(f"## ⚖️ Supply and Demand Market Simulator")
    st.markdown(
        "Agricultural prices fluctuate based on the fundamental balance between market arrivals (supply) "
        "and consumer absorption (demand). Test scenario shocks to observe price reactions."
    )

    curr_p = price_service.get_price_forecast(crop, mandi)["current_price"]

    # Interactive Sliders
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📦 Supply Parameters (Arrivals / Production)")
        base_s = st.number_input("Baseline Market Arrivals (Tonnes / day)", min_value=10.0, max_value=2000.0, value=120.0, step=10.0)
        new_s = st.slider("Simulated New Supply (Tonnes / day)", min_value=20.0, max_value=300.0, value=150.0, step=5.0)

    with c2:
        st.markdown("#### 🛒 Demand Parameters (Consumer / Industrial)")
        base_d = st.number_input("Baseline Demand Index", min_value=50.0, max_value=200.0, value=100.0, step=5.0)
        new_d = st.slider("Simulated New Demand Index", min_value=50.0, max_value=180.0, value=95.0, step=5.0)

    epsilon = sd_sim.DEFAULT_ELASTICITIES.get(crop, 0.55)
    
    # Run simulation
    sim = sd_sim.simulate(
        crop=crop,
        base_price=curr_p,
        base_supply_tonnes=base_s,
        new_supply_tonnes=new_s,
        base_demand_index=base_d,
        new_demand_index=new_d,
        custom_elasticity=epsilon
    )

    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Base Price", f"₹{sim['base_price']:,.0f} / q")
    with k2:
        st.metric("Simulated Equilibrium Price", f"₹{sim['new_simulated_price']:,.0f} / q", delta=f"{sim['price_change_pct']:+.1f}%")
    with k3:
        st.metric("Net Supply Shift", f"{sim['supply_change_pct']:+.1f}%", delta=f"{new_s - base_s:+.0f} Tonnes")
    with k4:
        st.metric("Market Equilibrium State", sim["market_state"])

    # Interactive Plotly Supply-Demand Curve
    st.markdown("### 📉 Economic Price Reaction Curve")
    
    # Generate supply range curve
    s_range = np.linspace(base_s * 0.4, base_s * 1.8, 50)
    prices_curve = [curr_p * ((new_d / base_d) / (s / base_s)) ** epsilon for s in s_range]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s_range,
        y=prices_curve,
        mode="lines",
        name="Price-Supply Sensitivity Curve",
        line=dict(color="#3b82f6", width=3)
    ))

    # Mark baseline point
    fig.add_trace(go.Scatter(
        x=[base_s],
        y=[curr_p],
        mode="markers+text",
        name="Baseline Equilibrium",
        marker=dict(size=12, color="#94a3b8"),
        text=["Baseline"],
        textposition="top right"
    ))

    # Mark new simulated point
    fig.add_trace(go.Scatter(
        x=[new_s],
        y=[sim["new_simulated_price"]],
        mode="markers+text",
        name="Simulated Scenario Point",
        marker=dict(size=14, color="#10b981" if sim["price_change_pct"] >= 0 else "#ef4444"),
        text=[f"Simulated: ₹{sim['new_simulated_price']:,.0f}"],
        textposition="top right"
    ))

    fig.update_layout(
        title=f"<b>Price Elasticity Response Curve for {crop} (Elasticity \u03b5 = {epsilon})</b>",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#e2e8f0"),
        xaxis=dict(title="Market Arrivals Supply (Tonnes)", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Price (₹ per Quintal)", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

