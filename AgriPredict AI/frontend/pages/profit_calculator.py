"""
Page: Farmer Profit Calculator & Storage Decision Simulator.
Calculates production expenses, break-even selling prices, and simulates
immediate selling vs storing for 7, 15, and 30 days.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any

from frontend.components.charts import create_profit_breakdown_waterfall
from backend.services.price_service import PriceService
from simulation.profit_simulator import FarmerProfitSimulator
from simulation.storage_simulator import StorageSimulator

def render_profit_calculator_page(settings: Dict[str, Any]):
    crop = settings["crop"]
    mandi = settings["mandi"]
    quantity = settings["quantity"]

    price_service = PriceService()
    profit_sim = FarmerProfitSimulator()
    storage_sim = StorageSimulator()

    st.markdown(f"## 💰 Farmer Profit & Storage Decision Simulator")
    st.markdown(
        "Calculate your true production cost of cultivation, break-even selling threshold, "
        "and determine whether storing crops in cold storage yields higher profits than immediate sale."
    )

    curr_p = price_service.get_price_forecast(crop, mandi)["current_price"]
    defaults = profit_sim.DEFAULT_CULTIVATION_BREAKDOWN.get(crop, profit_sim.DEFAULT_CULTIVATION_BREAKDOWN["Tomato"])
    est_acres = max(0.5, quantity / defaults["avg_yield_quintals_acre"])

    tab1, tab2 = st.tabs(["💵 Cultivation P&L Calculator", "❄️ Storage vs Immediate Sale"])

    with tab1:
        st.markdown("### 🚜 Cultivation Expenses (Input Parameters)")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            selling_price = st.number_input("Selling Price (₹ / Quintal)", min_value=300.0, max_value=15000.0, value=float(curr_p), step=50.0)
            seed_exp = st.number_input("Seeds & Saplings (₹)", min_value=500.0, max_value=50000.0, value=float(defaults["seeds_per_acre"] * est_acres), step=500.0)
            fert_exp = st.number_input("Fertilizers & Nutrients (₹)", min_value=1000.0, max_value=80000.0, value=float(defaults["fertilizer_per_acre"] * est_acres), step=500.0)
        with c2:
            pest_exp = st.number_input("Pesticides & Crop Protection (₹)", min_value=500.0, max_value=60000.0, value=float(defaults["pesticides_per_acre"] * est_acres), step=500.0)
            labour_exp = st.number_input("Labour & Harvesting (₹)", min_value=2000.0, max_value=100000.0, value=float(defaults["labour_per_acre"] * est_acres), step=1000.0)
            water_exp = st.number_input("Irrigation & Electricity (₹)", min_value=500.0, max_value=30000.0, value=float(defaults["irrigation_per_acre"] * est_acres), step=500.0)
        with c3:
            transport_exp = st.number_input("Freight & Transport (₹)", min_value=0.0, max_value=40000.0, value=float(quantity * 45.0), step=500.0)
            storage_exp = st.number_input("Storage Facility Fees (₹)", min_value=0.0, max_value=30000.0, value=0.0, step=200.0)
            mandi_cess = st.number_input("Mandi Cess & Commission (%)", min_value=0.0, max_value=5.0, value=1.5, step=0.1)

        # Calculate profit sheet
        p_res = profit_sim.calculate_profit(
            crop=crop,
            quantity_quintals=quantity,
            selling_price_per_q=selling_price,
            acres_cultivated=est_acres,
            custom_seed_cost=seed_exp,
            custom_fertilizer_cost=fert_exp,
            custom_pesticide_cost=pest_exp,
            custom_labour_cost=labour_exp,
            custom_irrigation_cost=water_exp,
            transport_cost_total=transport_exp,
            storage_cost_total=storage_exp,
            mandi_cess_pct=mandi_cess
        )

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Gross Revenue", f"₹{p_res['gross_revenue']:,.0f}")
        with m2:
            st.metric("Total Expenses", f"₹{p_res['total_expenses']:,.0f}")
        with m3:
            st.metric("Net Farm Profit", f"₹{p_res['net_profit']:,.0f}", delta=f"{p_res['profit_margin_pct']:.1f}% Margin")
        with m4:
            st.metric("Break-Even Price", f"₹{p_res['break_even_price_per_q']:,.0f} / q", delta=f"{p_res['financial_health']}")

        # Waterfall Chart
        fig = create_profit_breakdown_waterfall(p_res)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### ❄️ Storage Economics: Immediate Sale vs 7, 15, and 30 Days")
        st.write("Compare net profit after factoring cold storage fees and physiological weight/spoilage loss.")

        c_a, c_b = st.columns(2)
        with c_a:
            cold_storage = st.checkbox("Use Temperature-Controlled Cold Storage", value=True)
        with c_b:
            p7 = price_service.get_price_forecast(crop, mandi, horizon_days=7)["predicted_price"]
            p15 = price_service.get_price_forecast(crop, mandi, horizon_days=15)["predicted_price"]
            p30 = price_service.get_price_forecast(crop, mandi, horizon_days=30)["predicted_price"]

        stor_res = storage_sim.simulate_strategies(
            crop=crop,
            quantity_quintals=quantity,
            current_price=curr_p,
            price_7d=p7,
            price_15d=p15,
            price_30d=p30,
            use_cold_storage=cold_storage
        )

        st.info(f"💡 **AI Storage Advisory**: {stor_res['recommendation']}")

        # Strategy Table
        s_df = pd.DataFrame(stor_res["strategies"])
        s_display = s_df[[
            "strategy", "expected_price", "storage_cost", "spoilage_pct",
            "effective_quantity", "gross_revenue", "net_realization", "net_gain_vs_immediate", "gain_per_quintal"
        ]].copy()
        s_display.columns = [
            "Strategy", "Expected Price (₹/q)", "Storage Cost (₹)", "Spoilage Loss (%)",
            "Effective Qty (q)", "Gross Revenue (₹)", "Net Realization (₹)", "Net Gain vs Immediate (₹)", "Gain per Quintal (₹/q)"
        ]

        st.dataframe(
            s_display.style.highlight_max(subset=["Net Realization (₹)"], color="#064e3b")
            .format({
                "Expected Price (₹/q)": "₹{:,.0f}",
                "Storage Cost (₹)": "₹{:,.0f}",
                "Spoilage Loss (%)": "{:.1f}%",
                "Effective Qty (q)": "{:,.1f} q",
                "Gross Revenue (₹)": "₹{:,.0f}",
                "Net Realization (₹)": "₹{:,.0f}",
                "Net Gain vs Immediate (₹)": "{:+,.0f}",
                "Gain per Quintal (₹/q)": "{:+,.1f}"
            }),
            use_container_width=True
        )

