"""
Page: Market Comparison & Smart Transportation Optimization.
Compares crop prices across multiple agricultural mandis, calculates road distance,
freight charges, transit loss, and identifies highest net-yielding destination.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any

from frontend.components.charts import create_market_comparison_bar
from backend.services.price_service import PriceService
from recommendation.market_recommendation import MarketComparisonEngine

def render_market_analysis_page(settings: Dict[str, Any]):
    crop = settings["crop"]
    mandi = settings["mandi"]
    quantity = settings["quantity"]

    price_service = PriceService()
    comparison_engine = MarketComparisonEngine()

    st.markdown(f"## 🚛 Market Comparison & Transport Arbitrage")
    st.markdown(
        "Compare crop prices across regional agricultural mandis. The system calculates "
        "inter-mandi distance, truck freight, loading fees, and transit shrinkage to find the most profitable destination."
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        st.write(f"Evaluating freight logistics starting from origin mandi: **{mandi}**")
    with c2:
        diesel_mult = st.slider("Fuel / Freight Rate Multiplier", min_value=0.8, max_value=2.0, value=1.0, step=0.1, help="Simulate diesel price hikes on transport costs")

    # Fetch latest prices and run comparison
    latest_prices = price_service.get_all_market_prices_latest(crop)
    res = comparison_engine.compare_markets(
        crop=crop,
        origin_market=mandi,
        quantity_quintals=quantity,
        market_prices=latest_prices,
        diesel_cost_multiplier=diesel_mult
    )

    best_mkt = res["best_market"]
    best_gain = res["best_net_gain"]
    best_gain_q = res["best_net_gain_per_q"]

    if best_mkt == mandi:
        st.success(f"✅ **Optimal Destination: {mandi} (Local Market)**. Transporting to other mandis does not offset freight and transit costs.")
    else:
        st.warning(
            f"🚀 **Arbitrage Opportunity**: Transport to **{best_mkt}**! "
            f"Generates an estimated additional net profit of **+₹{best_gain:,.0f}** (+₹{best_gain_q:,.0f}/quintal) "
            f"after all transport and transit loss deductions."
        )

    # Plotly Bar Chart
    fig = create_market_comparison_bar(res["comparisons"], crop=crop)
    st.plotly_chart(fig, use_container_width=True)

    # Detailed Table
    st.markdown("### 📋 Mandi Transport Economics Breakdown")
    df = pd.DataFrame(res["comparisons"])
    show_df = df[[
        "market", "state", "distance_km", "quoted_price",
        "logistics_cost_per_q", "transit_loss_pct", "net_price_per_q", "net_advantage_vs_origin"
    ]].copy()
    show_df.columns = [
        "Mandi", "State", "Distance (km)", "Quoted Price (₹/q)",
        "Logistics Cost (₹/q)", "Transit Loss (%)", "Net Realization (₹/q)", "Net Advantage vs Origin (₹)"
    ]

    st.dataframe(
        show_df.style.highlight_max(subset=["Net Realization (₹/q)"], color="#064e3b")
        .format({
            "Distance (km)": "{:,.0f} km",
            "Quoted Price (₹/q)": "₹{:,.0f}",
            "Logistics Cost (₹/q)": "₹{:,.1f}",
            "Transit Loss (%)": "{:.1f}%",
            "Net Realization (₹/q)": "₹{:,.0f}",
            "Net Advantage vs Origin (₹)": "{:+,.0f}"
        }),
        use_container_width=True
    )

