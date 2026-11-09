"""
Page: What-If Macro Scenario Simulator & Agricultural Digital Twin.
Simulates parametric macro shocks (export bans, bumper harvests, logistics shocks)
and runs a multi-agent digital twin simulating farmers, traders, wholesalers, and retailers.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any

from backend.services.price_service import PriceService
from simulation.market_simulator import WhatIfMarketSimulator

def render_scenario_simulator_page(settings: Dict[str, Any]):
    crop = settings["crop"]
    mandi = settings["mandi"]

    price_service = PriceService()
    sim_engine = WhatIfMarketSimulator()

    st.markdown("## 🧪 What-If Scenario Simulator & Agricultural Digital Twin")
    st.markdown(
        "Test counterfactual macroeconomic, climatic, and trade policy scenarios. "
        "Observe how shocks ripple through supply chains and affect price realization."
    )

    curr_p = price_service.get_price_forecast(crop, mandi)["current_price"]

    sim_tab1, sim_tab2 = st.tabs(["🔮 What-If Scenario Builder", "🤖 Agricultural Digital Twin (Multi-Agent)"])

    with sim_tab1:
        st.markdown("### 🎛️ Scenario Shock Controls")

        c1, c2, c3 = st.columns(3)
        with c1:
            prod_change = st.slider("Crop Production Change (%)", min_value=-50.0, max_value=50.0, value=20.0, step=5.0, help="E.g. +30% bumper harvest or -20% pest attack")
            demand_change = st.slider("Consumer Demand Change (%)", min_value=-40.0, max_value=50.0, value=0.0, step=5.0, help="E.g. Festival demand surge or economic slowdown")
        with c2:
            rain_shock = st.slider("Rainfall Shock (%)", min_value=-60.0, max_value=80.0, value=-30.0, step=5.0, help="E.g. -40% drought or +50% flood")
            transport_mult = st.slider("Freight Transport Multiplier", min_value=1.0, max_value=2.5, value=1.2, step=0.1, help="E.g. 2.0x diesel price surge")
        with c3:
            export_ban = st.checkbox("Government Export Ban / Restriction", value=False, help="Restricts border exports, keeping inventory domestic")
            glut_arrivals = st.number_input("Sudden Market Glut (Extra Tonnes)", min_value=0.0, max_value=150.0, value=0.0, step=10.0)

        # Run what-if scenario
        res = sim_engine.simulate_scenario(
            crop=crop,
            base_price=curr_p,
            base_supply_tonnes=120.0,
            base_demand_index=100.0,
            production_change_pct=prod_change,
            demand_change_pct=demand_change,
            rainfall_anomaly_pct=rain_shock,
            transport_cost_multiplier=transport_mult,
            export_restricted=export_ban,
            sudden_glut_arrival_tonnes=glut_arrivals
        )

        st.markdown("---")
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Baseline Spot Price", f"₹{res['base_price']:,.0f} / q")
        with k2:
            st.metric("Simulated Mandi Price", f"₹{res['simulated_mandi_price']:,.0f} / q", delta=f"{res['price_delta_pct']:+.1f}%")
        with k3:
            st.metric("Farm-Gate Realization", f"₹{res['simulated_farm_gate_price']:,.0f} / q", delta=f"₹{res['simulated_farm_gate_price'] - res['base_price']:+,.0f}")
        with k4:
            st.metric("Terminal Retail Price", f"₹{res['simulated_consumer_price']:,.0f} / q")

        st.markdown("#### 💡 Scenario Analysis & Market Dynamics")
        for ins in res["insights"]:
            st.markdown(f"• **Market Finding**: {ins}")

    with sim_tab2:
        st.markdown("### 🌐 Multi-Agent Market Digital Twin")
        st.write(
            "Simulates microeconomic transactions across agents: Farmers placing asks, "
            "Commission Agents aggregating, Wholesalers bidding, and Retailers clearing inventory."
        )

        num_farmers = st.slider("Active Farmer Agents", min_value=20, max_value=150, value=50, step=10)
        
        twin_res = sim_engine.run_multi_agent_simulation(
            crop=crop,
            base_price=curr_p,
            num_farmers=num_farmers
        )

        d1, d2, d3 = st.columns(3)
        with d1:
            st.metric("Clearing Mandi Price", f"₹{twin_res['clearing_mandi_price']:,.0f} / q")
        with d2:
            st.metric("Final Consumer Retail Price", f"₹{twin_res['final_consumer_price']:,.0f} / q")
        with d3:
            st.metric("Farmer Share of Consumer Rupee", f"{twin_res['farmer_share_of_consumer_rupee']:.1f}%", help="Percentage of final consumer price received by farmer")

        # Value chain pie chart
        margin_df = pd.DataFrame(twin_res["margin_breakdown"])
        fig_pie = px.pie(
            margin_df,
            values="amount",
            names="stakeholder",
            title="<b>Value Chain Margin Distribution (Consumer Rupee Breakdown)</b>",
            color_discrete_sequence=["#10b981", "#3b82f6", "#f59e0b", "#a855f7"]
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#e2e8f0")
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.dataframe(
            margin_df.style.format({
                "amount": "₹{:,.1f}",
                "share_pct": "{:.1f}%"
            }),
            use_container_width=True
        )

