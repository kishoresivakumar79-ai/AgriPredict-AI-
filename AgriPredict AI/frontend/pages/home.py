"""
Page: Home / Executive Market Overview.
Presents top-level agricultural KPIs, live spot prices, AI recommendation banner,
and quick commodity summary.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any

from frontend.components.cards import render_metric_card, render_recommendation_banner
from backend.services.price_service import PriceService
from backend.services.recommendation_service import RecommendationService

def render_home_page(settings: Dict[str, Any]):
    crop = settings["crop"]
    mandi = settings["mandi"]
    horizon = settings["horizon"]
    model = settings["model"]
    quantity = settings["quantity"]

    price_service = PriceService()
    rec_service = RecommendationService()

    # Fetch live data and advisory
    advisory = rec_service.get_full_farmer_advisory(
        crop=crop,
        current_market=mandi,
        quantity_quintals=quantity,
        horizon_days=horizon
    )
    forecast = advisory["forecast"]
    decision = advisory["decision"]
    market_comp = advisory["market_comparison"]
    storage = advisory["storage_analysis"]

    curr_p = forecast["current_price"]
    pred_p = forecast["predicted_price"]
    p_chg = forecast["price_change_pct"]
    delta_str = f"{p_chg:+.1f}%"

    st.markdown(f"## 🌾 {crop} Market Intelligence & Price Forecast")
    st.markdown(f"**Selected Mandi**: `{mandi}` | **Prediction Target**: `{horizon} Days Ahead` | **AI Engine**: `{model}`")

    # Top-Level KPI Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            title="Current Spot Price",
            value=f"₹{curr_p:,.0f}",
            subtext=f"Mandi modal rate ({forecast.get('latest_record_date', 'Today')})",
            delta="Live Quote",
            icon="🏷️"
        )
    with c2:
        render_metric_card(
            title=f"Predicted Price ({horizon}d)",
            value=f"₹{pred_p:,.0f}",
            subtext=f"Range: ₹{forecast['pessimistic_price']:,.0f} - ₹{forecast['optimistic_price']:,.0f}",
            delta=delta_str,
            icon="🔮"
        )
    with c3:
        best_dest = market_comp["best_market"]
        best_gain = market_comp["best_net_gain_per_q"]
        render_metric_card(
            title="Best Market Destination",
            value=best_dest,
            subtext=f"{'Local market best' if best_dest == mandi else f'Net gain +₹{best_gain:,.0f}/q'}",
            delta=f"{'+₹' + str(int(best_gain)) + '/q' if best_gain > 0 else 'Optimal'}",
            icon="🚛"
        )
    with c4:
        imm_rev = curr_p * quantity
        proj_net = storage["max_net_realization"]
        net_diff = proj_net - imm_rev
        render_metric_card(
            title=f"Est. Farmer Net Revenue",
            value=f"₹{proj_net:,.0f}",
            subtext=f"For {quantity:,.0f} quintals harvest",
            delta=f"{'+₹' + str(int(net_diff)) if net_diff > 0 else 'Immediate Sale'}",
            icon="💰"
        )

    # Prominent AI Recommendation Banner
    render_recommendation_banner(
        action_headline=decision["headline"],
        urgency=decision["urgency"],
        risk_level=decision["risk_level"],
        confidence_score=decision["confidence_score_pct"],
        reasons=decision["reasons"]
    )

    # Next steps action list
    st.markdown("#### 📋 Recommended Action Plan for Farmers")
    for idx, step in enumerate(decision["action_steps"], 1):
        st.markdown(f"**Step {idx}**: {step}")

    st.markdown("---")
    # Live Rates Ticker across all mandis for this crop
    st.markdown(f"#### 📊 Regional Mandi Price Snapshot for {crop}")
    comp_df = pd.DataFrame(market_comp["comparisons"])
    display_df = comp_df[["market", "state", "quoted_price", "distance_km", "logistics_cost_per_q", "net_price_per_q", "advantage_per_q"]].copy()
    display_df.columns = ["Mandi", "State", "Quoted Price (₹/q)", "Distance (km)", "Freight & Toll (₹/q)", "Net Realization (₹/q)", "Advantage vs Origin (₹/q)"]
    
    st.dataframe(
        display_df.style.highlight_max(subset=["Net Realization (₹/q)"], color="#064e3b")
        .format({
            "Quoted Price (₹/q)": "₹{:,.0f}",
            "Distance (km)": "{:,.0f} km",
            "Freight & Toll (₹/q)": "₹{:,.1f}",
            "Net Realization (₹/q)": "₹{:,.0f}",
            "Advantage vs Origin (₹/q)": "₹{:,.0f}"
        }),
        use_container_width=True
    )

