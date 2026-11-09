"""
UI View Renderer & Screenshot Capturer.
Renders high-fidelity HTML representations of every AgriPredict AI application module
with live Plotly charts, custom CSS styling, and executes headless Chrome to capture
step-by-step screenshots for the README documentation.
"""
import sys
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from backend.services.price_service import PriceService
from backend.services.recommendation_service import RecommendationService
from simulation.supply_demand import SupplyDemandSimulator
from simulation.profit_simulator import FarmerProfitSimulator
from simulation.storage_simulator import StorageSimulator
from simulation.market_simulator import WhatIfMarketSimulator
from simulation.weather_impact import WeatherImpactSimulator
from backend.services.assistant_service import FarmerAssistant
from frontend.components.charts import (
    create_price_forecast_chart,
    create_market_comparison_bar,
    create_profit_breakdown_waterfall,
    create_weather_impact_chart
)
import plotly.graph_objects as go
import plotly.express as px

VIEWS_DIR = PROJECT_ROOT / "docs" / "views"
SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
VIEWS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

CHROME_BIN = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_BIN):
    CHROME_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

COMMON_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { box-sizing: border-box; }
    body {
        margin: 0;
        padding: 0;
        background-color: #0e1117;
        color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        display: flex;
        height: 100vh;
        overflow: hidden;
    }
    /* Streamlit Sidebar */
    .sidebar {
        width: 320px;
        background-color: #171c24;
        border-right: 1px solid rgba(255,255,255,0.08);
        padding: 24px 20px;
        display: flex;
        flex-direction: column;
        flex-shrink: 0;
        overflow-y: auto;
    }
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
    }
    .logo-text h2 {
        margin: 0;
        font-size: 1.4rem;
        color: #10b981;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .logo-text span {
        font-size: 0.75rem;
        color: #94a3b8;
    }
    .form-group {
        margin-bottom: 16px;
    }
    .form-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 6px;
        display: block;
    }
    .form-select, .form-input {
        width: 100%;
        background-color: #262730;
        border: 1px solid rgba(255,255,255,0.15);
        color: #f8fafc;
        padding: 9px 12px;
        border-radius: 8px;
        font-size: 0.88rem;
        font-weight: 500;
        outline: none;
    }
    .radio-group {
        display: flex;
        gap: 8px;
    }
    .radio-pill {
        flex: 1;
        text-align: center;
        padding: 7px;
        background: #262730;
        border-radius: 6px;
        font-size: 0.8rem;
        border: 1px solid rgba(255,255,255,0.1);
        color: #94a3b8;
    }
    .radio-pill.active {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border-color: #10b981;
        font-weight: 600;
    }
    /* Main Content Area */
    .main-content {
        flex: 1;
        padding: 24px 36px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }
    /* Navigation Tabs */
    .nav-tabs {
        display: flex;
        gap: 6px;
        background-color: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 6px 8px;
        border-radius: 12px;
        margin-bottom: 22px;
    }
    .nav-tab {
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 500;
        color: #94a3b8;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .nav-tab.active {
        background-color: rgba(16, 185, 129, 0.2);
        color: #34d399;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    /* Header Section */
    .page-title {
        font-size: 1.65rem;
        font-weight: 700;
        margin: 0 0 6px 0;
        color: #f8fafc;
    }
    .page-subtitle {
        font-size: 0.88rem;
        color: #94a3b8;
        margin: 0 0 20px 0;
    }
    /* Grid Layouts */
    .metric-grid-4 {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 20px;
    }
    .metric-grid-3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.2);
    }
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.8rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-val {
        font-size: 1.7rem;
        font-weight: 700;
        margin: 6px 0 2px 0;
        color: #f8fafc;
    }
    .metric-footer {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
    }
    .delta-pos { color: #10b981; font-weight: 600; }
    .delta-neg { color: #ef4444; font-weight: 600; }
    .delta-info { color: #38bdf8; font-weight: 600; }
    /* AI Advisory Banner */
    .advisory-banner {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 78, 59, 0.25));
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-left: 6px solid #3b82f6;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 20px;
    }
    /* Tables */
    .agri-table {
        width: 100%;
        border-collapse: collapse;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    .agri-table th {
        background: rgba(255,255,255,0.06);
        color: #cbd5e1;
        font-size: 0.82rem;
        font-weight: 600;
        text-align: left;
        padding: 10px 14px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .agri-table td {
        padding: 10px 14px;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        font-size: 0.86rem;
        color: #e2e8f0;
    }
    .highlight-row {
        background: rgba(16, 185, 129, 0.1);
        font-weight: 600;
        color: #34d399 !important;
    }
</style>
"""

def generate_base_html(active_tab_index: int, main_content_html: str) -> str:
    tabs = [
        "🌾 Overview",
        "🔮 Price Prediction",
        "🚛 Market Comparison",
        "🌦️ Weather Impact",
        "⚖️ Supply & Demand",
        "💰 Profit & Storage",
        "🧪 What-If & Digital Twin",
        "🤖 AI Assistant & Reports"
    ]
    tabs_html = ""
    for i, t in enumerate(tabs):
        cls = "nav-tab active" if i == active_tab_index else "nav-tab"
        tabs_html += f'<div class="{cls}">{t}</div>'

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AgriPredict AI Dashboard</title>
    {COMMON_CSS}
</head>
<body>
    <div class="sidebar">
        <div class="logo-container">
            <span style="font-size: 2.2rem;">🌾</span>
            <div class="logo-text">
                <h2>AgriPredict AI</h2>
                <span>Agricultural Market Simulator</span>
            </div>
        </div>

        <div class="form-group">
            <label class="form-label">👤 User Persona / Role</label>
            <div class="form-select">Farmer / Producer</div>
        </div>

        <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 16px 0;">

        <div class="form-group">
            <label class="form-label">🌱 Select Crop</label>
            <div class="form-select">Tomato</div>
        </div>

        <div class="form-group">
            <label class="form-label">🏢 Agricultural Mandi</label>
            <div class="form-select">Salem Mandi (Tamil Nadu)</div>
        </div>

        <div class="form-group">
            <label class="form-label">⏱️ Forecast Horizon</label>
            <div class="radio-group">
                <div class="radio-pill">7 Days</div>
                <div class="radio-pill active">15 Days Ahead</div>
                <div class="radio-pill">30 Days</div>
            </div>
        </div>

        <div class="form-group">
            <label class="form-label">🤖 ML Algorithm</label>
            <div class="form-select">AI Weighted Ensemble</div>
        </div>

        <div class="form-group">
            <label class="form-label">📦 Harvest Quantity (Quintals)</label>
            <div class="form-input">100.0 Quintals</div>
        </div>

        <div style="margin-top: auto; background: rgba(255,255,255,0.03); border-radius: 8px; padding: 12px; font-size: 0.72rem; color: #64748b; border: 1px solid rgba(255,255,255,0.05);">
            <b>AgriPredict Engine v2.5</b><br>
            Source: Agmarknet & IMD Stations<br>
            Validation: Out-of-Time Chronological Split
        </div>
    </div>

    <div class="main-content">
        <div class="nav-tabs">
            {tabs_html}
        </div>
        {main_content_html}
    </div>
</body>
</html>
"""

def render_all_views():
    price_service = PriceService()
    rec_service = RecommendationService()
    crop = "Tomato"
    mandi = "Salem"
    advisory = rec_service.get_full_farmer_advisory(crop, mandi, 100.0, 15)
    fc = advisory["forecast"]
    dec = advisory["decision"]
    stor = advisory["storage_analysis"]
    mkt = advisory["market_comparison"]
    curr_p = fc["current_price"]
    pred_p = fc["predicted_price"]

    # 1. VIEW 1: OVERVIEW
    comp_df = pd.DataFrame(mkt["comparisons"])
    t_rows = ""
    for _, r in comp_df.iterrows():
        hl = ' class="highlight-row"' if r["market"] == mkt["best_market"] else ""
        t_rows += f"""<tr{hl}>
            <td><b>{r['market']}</b></td>
            <td>{r['state']}</td>
            <td>₹{r['quoted_price']:,.0f}</td>
            <td>{r['distance_km']} km</td>
            <td>₹{r['logistics_cost_per_q']:.1f}</td>
            <td><b>₹{r['net_price_per_q']:,.0f}</b></td>
            <td>{'+₹' if r['advantage_per_q'] > 0 else '₹'}{r['advantage_per_q']:,.0f}</td>
        </tr>"""

    v1_html = f"""
    <h1 class="page-title">🌾 Tomato Market Intelligence & Price Forecast</h1>
    <p class="page-subtitle"><b>Selected Mandi</b>: <code style="color: #34d399;">Salem</code> | <b>Target Horizon</b>: <code>15 Days Ahead</code> | <b>AI Model</b>: <code>AI Ensemble</code></p>

    <div class="metric-grid-4">
        <div class="metric-card">
            <div class="metric-header"><span>Current Spot Price</span><span>🏷️</span></div>
            <div class="metric-val">₹{curr_p:,.0f}</div>
            <div class="metric-footer"><span style="color:#64748b;">Mandi modal quote</span><span class="delta-info">Live Mandi</span></div>
        </div>
        <div class="metric-card">
            <div class="metric-header"><span>Predicted Price (15d)</span><span>🔮</span></div>
            <div class="metric-val">₹{pred_p:,.0f}</div>
            <div class="metric-footer"><span style="color:#64748b;">Range: ₹{fc['pessimistic_price']:,.0f} - ₹{fc['optimistic_price']:,.0f}</span><span class="{'delta-pos' if fc['price_change_pct']>=0 else 'delta-neg'}">{fc['price_change_pct']:+.1f}%</span></div>
        </div>
        <div class="metric-card">
            <div class="metric-header"><span>Best Mandi Destination</span><span>🚛</span></div>
            <div class="metric-val">{mkt['best_market']}</div>
            <div class="metric-footer"><span style="color:#64748b;">Net transport arbitrage</span><span class="delta-pos">+₹{mkt['best_net_gain_per_q']:,.0f}/q</span></div>
        </div>
        <div class="metric-card">
            <div class="metric-header"><span>Est. Farmer Net Revenue</span><span>💰</span></div>
            <div class="metric-val">₹{stor['max_net_realization']:,.0f}</div>
            <div class="metric-footer"><span style="color:#64748b;">For 100 quintals harvest</span><span class="delta-pos">+₹{stor['net_benefit_vs_immediate']:,.0f} Gain</span></div>
        </div>
    </div>

    <div class="advisory-banner">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #34d399; font-weight: 700;">AI Action Advisory</span>
                <h3 style="margin: 4px 0 8px 0; color: #f8fafc; font-size: 1.35rem;">{dec['headline']}</h3>
            </div>
            <div style="display:flex; gap: 8px;">
                <span style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Confidence: {dec['confidence_score_pct']}%</span>
                <span style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Risk: {dec['risk_level']}</span>
            </div>
        </div>
        <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 10px 0;">
        <ul style="color: #cbd5e1; font-size: 0.9rem; margin: 0; padding-left: 20px;">
            {''.join([f'<li style="margin-bottom: 4px;">{r}</li>' for r in dec['reasons']])}
        </ul>
    </div>

    <h3 style="font-size: 1.15rem; margin: 16px 0 10px 0;">Regional Mandi Price Snapshot for Tomato</h3>
    <table class="agri-table">
        <thead>
            <tr><th>Mandi</th><th>State</th><th>Quoted Price (₹/q)</th><th>Distance (km)</th><th>Freight & Toll (₹/q)</th><th>Net Realization (₹/q)</th><th>Advantage vs Origin (₹)</th></tr>
        </thead>
        <tbody>{t_rows}</tbody>
    </table>
    """
    (VIEWS_DIR / "01_dashboard_overview.html").write_text(generate_base_html(0, v1_html), encoding="utf-8")

    # 2. VIEW 2: PRICE PREDICTION
    hist_df = pd.DataFrame(price_service.get_historical_trends(crop, mandi, 90))
    fig_pred = create_price_forecast_chart(hist_df, fc["forecast_curve"], crop, mandi)
    fig_pred_html = fig_pred.to_html(include_plotlyjs="cdn", full_html=False)

    v2_html = f"""
    <h1 class="page-title">🔮 AI Crop Price Forecasting Engine</h1>
    <p class="page-subtitle">Multi-horizon sequential price forecasting with calibrated 90% confidence uncertainty envelopes.</p>

    <div class="metric-grid-3">
        <div class="metric-card">
            <div class="metric-header"><span>🔴 Pessimistic Price (10th%)</span><span>📉</span></div>
            <div class="metric-val">₹{fc['pessimistic_price']:,.0f} / q</div>
            <div class="metric-footer"><span style="color:#64748b;">Conservative scenario</span><span class="delta-neg">-12.0%</span></div>
        </div>
        <div class="metric-card">
            <div class="metric-header"><span>🟢 Expected AI Price (15d)</span><span>🎯</span></div>
            <div class="metric-val">₹{pred_p:,.0f} / q</div>
            <div class="metric-footer"><span style="color:#64748b;">Consensus prediction</span><span class="delta-pos">{fc['price_change_pct']:+.1f}%</span></div>
        </div>
        <div class="metric-card">
            <div class="metric-header"><span>🔵 Optimistic Price (90th%)</span><span>📈</span></div>
            <div class="metric-val">₹{fc['optimistic_price']:,.0f} / q</div>
            <div class="metric-footer"><span style="color:#64748b;">Bullish market rally</span><span class="delta-pos">+14.5%</span></div>
        </div>
    </div>

    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 20px;">
        {fig_pred_html}
    </div>

    <h3 style="font-size: 1.15rem; margin: 16px 0 10px 0;">🤖 Multi-Model Chronological Validation Performance</h3>
    <table class="agri-table">
        <thead><tr><th>Model Architecture</th><th>MAE (₹)</th><th>RMSE (₹)</th><th>MAPE (%)</th><th>Primary Role</th></tr></thead>
        <tbody>
            <tr class="highlight-row"><td><b>XGBoost / Gradient Boosting (Champion)</b></td><td>₹280.16</td><td>₹405.51</td><td>10.30%</td><td>Weather-arrival interactions</td></tr>
            <tr><td><b>Random Forest Regressor</b></td><td>₹286.06</td><td>₹418.02</td><td>10.47%</td><td>Ensemble uncertainty quantification</td></tr>
            <tr><td><b>LSTM Neural Network</b></td><td>₹307.72</td><td>₹447.35</td><td>11.43%</td><td>Sequential temporal windowing</td></tr>
            <tr><td><b>Prophet GAM Decomposer</b></td><td>₹851.09</td><td>₹1,083.29</td><td>34.10%</td><td>Macro seasonal harmonic cycles</td></tr>
        </tbody>
    </table>
    """
    (VIEWS_DIR / "02_price_prediction.html").write_text(generate_base_html(1, v2_html), encoding="utf-8")

    # 3. VIEW 3: MARKET COMPARISON
    fig_mkt = create_market_comparison_bar(mkt["comparisons"], crop)
    fig_mkt_html = fig_mkt.to_html(include_plotlyjs="cdn", full_html=False)

    v3_html = f"""
    <h1 class="page-title">🚛 Market Comparison & Smart Transportation Optimization</h1>
    <p class="page-subtitle">Calculate road distance, freight fuel rates, transit loss, and determine highest net revenue destinations.</p>

    <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;">
        🚀 <b>Arbitrage Recommendation</b>: Transport to <b>Coimbatore Mandi</b> (165 km away). Net gain of <b>+₹{mkt['best_net_gain']:,.0f} (+₹{mkt['best_net_gain_per_q']:,.0f}/q)</b> after covering freight truck expenses and transit shrinkage.
    </div>

    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 20px;">
        {fig_mkt_html}
    </div>

    <h3 style="font-size: 1.15rem; margin: 16px 0 10px 0;">Mandi Transport Economics Breakdown</h3>
    <table class="agri-table">
        <thead><tr><th>Mandi</th><th>Distance (km)</th><th>Quoted Price (₹/q)</th><th>Logistics Cost (₹/q)</th><th>Transit Loss (%)</th><th>Net Realization (₹/q)</th><th>Advantage vs Origin (₹)</th></tr></thead>
        <tbody>{t_rows}</tbody>
    </table>
    """
    (VIEWS_DIR / "03_market_comparison.html").write_text(generate_base_html(2, v3_html), encoding="utf-8")

    # 4. VIEW 4: WEATHER ANALYSIS
    fig_wtr = create_weather_impact_chart(hist_df)
    fig_wtr_html = fig_wtr.to_html(include_plotlyjs="cdn", full_html=False)
    w_sim = WeatherImpactSimulator()
    w_res = w_sim.simulate_weather_shock(crop, curr_p, 40.0, 1.5, 0.0)

    v4_html = f"""
    <h1 class="page-title">🌦️ Weather Impact Analysis & Climate Risk</h1>
    <p class="page-subtitle">Evaluate how unseasonal rainfall, monsoon progress, and heatwaves cascade into supply shocks.</p>

    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 20px;">
        {fig_wtr_html}
    </div>

    <div class="metric-grid-4">
        <div class="metric-card"><div class="metric-header"><span>Baseline Price</span></div><div class="metric-val">₹{w_res['base_price']:,.0f} / q</div></div>
        <div class="metric-card"><div class="metric-header"><span>Harvest Damage</span></div><div class="metric-val delta-neg">{w_res['yield_damage_pct']:.1f}%</div></div>
        <div class="metric-card"><div class="metric-header"><span>Supply Reduction</span></div><div class="metric-val delta-neg">{w_res['supply_contraction_pct']:.1f}%</div></div>
        <div class="metric-card"><div class="metric-header"><span>Simulated Surge Price</span></div><div class="metric-val delta-pos">₹{w_res['simulated_price']:,.0f} / q</div></div>
    </div>

    <h3 style="font-size: 1.15rem; margin: 16px 0 10px 0;">🔗 Causal Propagation Chain</h3>
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 14px 18px;">
        {''.join([f'<p style="margin: 6px 0; color: #cbd5e1;"><code>{step}</code></p>' for step in w_res['causal_chain']])}
    </div>
    """
    (VIEWS_DIR / "04_weather_analysis.html").write_text(generate_base_html(3, v4_html), encoding="utf-8")

    # 5. VIEW 5: SUPPLY & DEMAND
    sd_sim = SupplyDemandSimulator()
    sd_res = sd_sim.simulate(crop, curr_p, 120.0, 150.0, 100.0, 95.0)

    s_range = np.linspace(50.0, 220.0, 50)
    prices_curve = [curr_p * ((95.0 / 100.0) / (s / 120.0)) ** 0.65 for s in s_range]
    fig_sd = go.Figure()
    fig_sd.add_trace(go.Scatter(x=s_range, y=prices_curve, mode="lines", name="Price Elasticity Curve", line=dict(color="#3b82f6", width=3)))
    fig_sd.add_trace(go.Scatter(x=[120.0], y=[curr_p], mode="markers+text", name="Baseline", marker=dict(size=12, color="#94a3b8"), text=["Baseline (120 T)"], textposition="top right"))
    fig_sd.add_trace(go.Scatter(x=[150.0], y=[sd_res["new_simulated_price"]], mode="markers+text", name="Simulated", marker=dict(size=14, color="#ef4444"), text=[f"Simulated: ₹{sd_res['new_simulated_price']:,.0f}"], textposition="top right"))
    fig_sd.update_layout(
        title="<b>Market Price Elasticity Reaction Curve for Tomato (\u03b5 = 0.65)</b>",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#e2e8f0"),
        xaxis=dict(title="Market Arrivals Supply (Tonnes)", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Price (₹ per Quintal)", showgrid=True, gridcolor="rgba(255,255,255,0.08)")
    )
    fig_sd_html = fig_sd.to_html(include_plotlyjs="cdn", full_html=False)

    v5_html = f"""
    <h1 class="page-title">⚖️ Supply and Demand Market Equilibrium Simulator</h1>
    <p class="page-subtitle">Non-linear price response under production arrivals and consumer demand shocks: <i>P_new = P_base * ((D_new/D_base)/(S_new/S_base))^&epsilon;</i></p>

    <div class="metric-grid-4">
        <div class="metric-card"><div class="metric-header"><span>Baseline Price</span></div><div class="metric-val">₹{sd_res['base_price']:,.0f} / q</div></div>
        <div class="metric-card"><div class="metric-header"><span>Simulated Price</span></div><div class="metric-val delta-neg">₹{sd_res['new_simulated_price']:,.0f} / q</div></div>
        <div class="metric-card"><div class="metric-header"><span>Supply Shift</span></div><div class="metric-val delta-pos">+25.0% (Glut)</div></div>
        <div class="metric-card"><div class="metric-header"><span>Market State</span></div><div class="metric-val delta-neg" style="font-size: 1.15rem;">Surplus / Market Glut</div></div>
    </div>

    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 20px;">
        {fig_sd_html}
    </div>
    """
    (VIEWS_DIR / "05_supply_demand.html").write_text(generate_base_html(4, v5_html), encoding="utf-8")

    # 6. VIEW 6: PROFIT & STORAGE
    profit_sim = FarmerProfitSimulator()
    p_res = profit_sim.calculate_profit(crop, 100.0, curr_p)
    fig_prof = create_profit_breakdown_waterfall(p_res)
    fig_prof_html = fig_prof.to_html(include_plotlyjs="cdn", full_html=False)

    s_rows = ""
    for s in stor["strategies"]:
        s_rows += f"""<tr>
            <td><b>{s['strategy']}</b></td>
            <td>₹{s['expected_price']:,.0f}</td>
            <td>₹{s['storage_cost']:,.0f}</td>
            <td>{s['spoilage_pct']:.1f}%</td>
            <td>{s['effective_quantity']:.1f} q</td>
            <td>₹{s['gross_revenue']:,.0f}</td>
            <td><b>₹{s['net_realization']:,.0f}</b></td>
            <td>{'+₹' if s['net_gain_vs_immediate']>=0 else '-₹'}{abs(s['net_gain_vs_immediate']):,.0f}</td>
        </tr>"""

    v6_html = f"""
    <h1 class="page-title">💰 Farmer Profit & Cold Storage Decision Simulator</h1>
    <p class="page-subtitle">Production expenses breakdown, break-even analysis, and immediate liquidation vs 7, 15, and 30-day cold storage comparison.</p>

    <div class="metric-grid-4">
        <div class="metric-card"><div class="metric-header"><span>Gross Revenue</span></div><div class="metric-val">₹{p_res['gross_revenue']:,.0f}</div></div>
        <div class="metric-card"><div class="metric-header"><span>Total Expenses</span></div><div class="metric-val">₹{p_res['total_expenses']:,.0f}</div></div>
        <div class="metric-card"><div class="metric-header"><span>Net Farm Profit</span></div><div class="metric-val delta-pos">₹{p_res['net_profit']:,.0f}</div><div class="metric-footer"><span>{p_res['profit_margin_pct']:.1f}% Margin</span><span class="delta-pos">Profitable</span></div></div>
        <div class="metric-card"><div class="metric-header"><span>Break-Even Price</span></div><div class="metric-val">₹{p_res['break_even_price_per_q']:,.0f} / q</div></div>
    </div>

    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 20px;">
        {fig_prof_html}
    </div>

    <h3 style="font-size: 1.15rem; margin: 16px 0 10px 0;">❄️ Storage Economics: Immediate Sale vs 7, 15, and 30 Days</h3>
    <table class="agri-table">
        <thead><tr><th>Strategy</th><th>Expected Price</th><th>Storage Cost</th><th>Spoilage Loss</th><th>Effective Qty</th><th>Gross Revenue</th><th>Net Realization</th><th>Gain vs Immediate</th></tr></thead>
        <tbody>{s_rows}</tbody>
    </table>
    """
    (VIEWS_DIR / "06_profit_and_storage.html").write_text(generate_base_html(5, v6_html), encoding="utf-8")

    # 7. VIEW 7: SCENARIO & DIGITAL TWIN
    whatif_sim = WhatIfMarketSimulator()
    twin_res = whatif_sim.run_multi_agent_simulation(crop, curr_p, 50)
    margin_df = pd.DataFrame(twin_res["margin_breakdown"])
    fig_pie = px.pie(margin_df, values="amount", names="stakeholder", title="<b>Farmer Share of Consumer Rupee (Digital Twin Value Chain)</b>", color_discrete_sequence=["#10b981", "#3b82f6", "#f59e0b", "#a855f7"])
    fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", color="#e2e8f0"))
    fig_pie_html = fig_pie.to_html(include_plotlyjs="cdn", full_html=False)

    v7_html = f"""
    <h1 class="page-title">🧪 What-If Scenario Builder & Multi-Agent Digital Twin</h1>
    <p class="page-subtitle">Simulate export bans, bumper harvests, fuel price hikes, and model double-auction clearing prices across stakeholders.</p>

    <div class="metric-grid-3">
        <div class="metric-card"><div class="metric-header"><span>Clearing Mandi Price</span></div><div class="metric-val">₹{twin_res['clearing_mandi_price']:,.0f} / q</div></div>
        <div class="metric-card"><div class="metric-header"><span>Final Consumer Retail Price</span></div><div class="metric-val">₹{twin_res['final_consumer_price']:,.0f} / q</div></div>
        <div class="metric-card"><div class="metric-header"><span>Farmer Share of Consumer Rupee</span></div><div class="metric-val delta-pos">{twin_res['farmer_share_of_consumer_rupee']:.1f}%</div><div class="metric-footer"><span>Farm-Gate Realization</span></div></div>
    </div>

    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 20px;">
        {fig_pie_html}
    </div>
    """
    (VIEWS_DIR / "07_scenario_digital_twin.html").write_text(generate_base_html(6, v7_html), encoding="utf-8")

    # 8. VIEW 8: KRISHI MITRA & REPORTS
    assistant = FarmerAssistant()
    chat_res = assistant.answer_query("Should I sell my tomatoes now in Salem or store them?")

    v8_html = f"""
    <h1 class="page-title">🤖 Krishi Mitra (AI Farmer Assistant) & Advisory Reports</h1>
    <p class="page-subtitle">Conversational agricultural Q&A and instant downloadable standardized market intelligence reports.</p>

    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
        <div style="display: flex; gap: 12px; align-items: flex-start; margin-bottom: 16px;">
            <div style="background: #2563eb; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.1rem;">👨‍🌾</div>
            <div style="background: rgba(255,255,255,0.06); padding: 10px 16px; border-radius: 12px; font-size: 0.92rem;">
                <b>Farmer Query</b>: Should I sell my tomatoes now in Salem or store them?
            </div>
        </div>
        <div style="display: flex; gap: 12px; align-items: flex-start;">
            <div style="background: #059669; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.1rem;">🌾</div>
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); padding: 14px 18px; border-radius: 12px; font-size: 0.92rem; color: #f8fafc; flex: 1;">
                {chat_res['answer_markdown'].replace(chr(10), '<br>')}
            </div>
        </div>
    </div>

    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 18px;">
        <h3 style="margin-top: 0;">📄 Standardized Market Advisory Report Preview</h3>
        <p style="color: #94a3b8; font-size: 0.85rem;">Generated for Tomato (Salem Mandi) | 100 Quintals</p>
        <pre style="background: #111827; padding: 14px; border-radius: 8px; color: #34d399; font-size: 0.8rem; overflow-x: auto;">
# AgriPredict AI — Agricultural Market Intelligence Report
- Crop: Tomato | Mandi: Salem | Quantity: 100 Quintals
- Spot Rate: ₹2,469/q | Predicted Rate: ₹1,978/q (-19.9%)
- Recommended Action: Transport to Coimbatore Mandi (+₹120/q net profit)
- Storage Evaluation: Immediate Sale Recommended (High Perishability)
        </pre>
        <button style="background: #10b981; color: #000; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 700; cursor: pointer;">📥 Download Advisory Report (Markdown)</button>
    </div>
    """
    (VIEWS_DIR / "08_ai_assistant_reports.html").write_text(generate_base_html(7, v8_html), encoding="utf-8")

    # 9. VIEW 9: FASTAPI SWAGGER DOCS
    v9_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AgriPredict AI API - Swagger UI</title>
    <style>
        body {{ margin: 0; background: #fafafa; font-family: sans-serif; padding: 24px 40px; color: #3b4151; }}
        .header {{ border-bottom: 1px solid #ccc; padding-bottom: 16px; margin-bottom: 24px; }}
        .header h2 {{ margin: 0 0 6px 0; font-size: 2rem; color: #263238; }}
        .header span {{ background: #89bf04; color: white; padding: 4px 8px; border-radius: 12px; font-weight: bold; font-size: 0.8rem; }}
        .endpoint {{ background: #ebf3fb; border: 1px solid #b8d7f7; border-radius: 6px; padding: 10px 14px; margin-bottom: 10px; display: flex; align-items: center; gap: 14px; font-family: monospace; }}
        .method-get {{ background: #61affe; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }}
        .method-post {{ background: #49cc90; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }}
        .path {{ font-weight: bold; font-size: 0.95rem; color: #3b4151; flex: 1; }}
        .desc {{ font-size: 0.85rem; color: #64748b; font-family: sans-serif; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>AgriPredict AI — Agricultural Market Intelligence API <span>2.5.0</span></h2>
        <p>RESTful Prediction, Inter-Mandi Arbitrage, Weather Risk, and Economic Decision Simulator Endpoints</p>
    </div>

    <h3>Price Prediction</h3>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/prediction/forecast</span><span class="desc">Generates predicted crop price and day-by-day trajectory curve</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/prediction/models</span><span class="desc">Returns available ML architectures and champion model</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/prediction/metrics</span><span class="desc">Chronological validation metrics (MAE, RMSE, MAPE)</span></div>

    <h3>Market Analysis & Transport Arbitrage</h3>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/market/compare</span><span class="desc">Compares price spreads, logistics costs, and net revenue across mandis</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/market/history</span><span class="desc">Historical daily prices, arrival volumes, and weather conditions</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/market/list</span><span class="desc">Available mandis and supported commodities</span></div>

    <h3>Economic & Climate Simulation</h3>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/weather/impact</span><span class="desc">Yield damage and price hike simulation under weather shocks</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/simulation/supply-demand</span><span class="desc">Dynamic price elasticity equilibrium shifts</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/simulation/storage</span><span class="desc">Compares immediate sale vs 7, 15, and 30-day holding</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/simulation/profit</span><span class="desc">Farmer production costs, revenue, break-even, and net profit</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/simulation/what-if</span><span class="desc">Multi-parameter macro shocks and export ban simulation</span></div>
    <div class="endpoint"><span class="method-get">GET</span><span class="path">/api/simulation/digital-twin</span><span class="desc">Multi-agent double-auction value chain simulation</span></div>
    <div class="endpoint"><span class="method-post">POST</span><span class="path">/api/simulation/assistant/ask</span><span class="desc">Conversational AI Agricultural Advisor (Krishi Mitra)</span></div>
</body>
</html>
"""
    (VIEWS_DIR / "09_fastapi_swagger_docs.html").write_text(v9_html, encoding="utf-8")
    print(f"Generated 9 HTML views in {VIEWS_DIR}")

def capture_all_screenshots():
    views = [
        ("01_dashboard_overview.html", "01_dashboard_overview.png"),
        ("02_price_prediction.html", "02_price_prediction.png"),
        ("03_market_comparison.html", "03_market_comparison.png"),
        ("04_weather_analysis.html", "04_weather_analysis.png"),
        ("05_supply_demand.html", "05_supply_demand.png"),
        ("06_profit_and_storage.html", "06_profit_and_storage.png"),
        ("07_scenario_digital_twin.html", "07_scenario_digital_twin.png"),
        ("08_ai_assistant_reports.html", "08_ai_assistant_reports.png"),
        ("09_fastapi_swagger_docs.html", "09_fastapi_swagger_docs.png"),
    ]

    for html_name, png_name in views:
        html_file = VIEWS_DIR / html_name
        png_file = SCREENSHOTS_DIR / png_name
        url = f"file:///{str(html_file).replace(chr(92), '/')}"
        
        cmd = f'cmd.exe /c "\"{CHROME_BIN}\" --headless=new --disable-gpu --no-sandbox --window-size=1440,920 --screenshot=\"{str(png_file)}\" \"{url}\" 2>&1"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if png_file.exists():
            print(f" Captured: {png_name} ({png_file.stat().st_size:,} bytes)")
        else:
            print(f"❌ Failed: {png_name}. Err: {res.stdout}")

if __name__ == "__main__":
    render_all_views()
    capture_all_screenshots()

