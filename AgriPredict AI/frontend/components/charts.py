"""
UI Component: Interactive Plotly Visualizations for Agricultural Intelligence.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

AGRI_THEME = {
    "bg_color": "rgba(0,0,0,0)",
    "paper_color": "rgba(0,0,0,0)",
    "font_family": "Inter, Roboto, sans-serif",
    "font_color": "#e2e8f0",
    "grid_color": "rgba(255,255,255,0.08)",
    "primary_green": "#10b981",
    "secondary_blue": "#3b82f6",
    "accent_amber": "#f59e0b",
    "danger_red": "#ef4444"
}

def create_price_forecast_chart(
    historical_df: pd.DataFrame,
    forecast_curve: List[Dict[str, Any]],
    crop: str,
    market: str
) -> go.Figure:
    """
    Renders historical price track + future predicted trajectory with shaded confidence envelope.
    """
    fig = go.Figure()

    # Historical Prices (last 45 days)
    hist_tail = historical_df.tail(45).copy()
    fig.add_trace(go.Scatter(
        x=hist_tail["date"],
        y=hist_tail["modal_price"],
        mode="lines",
        name="Historical Price",
        line=dict(color="#94a3b8", width=2.5),
        hovertemplate="<b>Date</b>: %{x}<br><b>Actual Price</b>: ₹%{y:,.0f}/q<extra></extra>"
    ))

    if forecast_curve:
        f_df = pd.DataFrame(forecast_curve)
        
        # Connect last historical point to first forecast point
        last_hist_date = hist_tail["date"].iloc[-1]
        last_hist_price = hist_tail["modal_price"].iloc[-1]
        
        dates = [last_hist_date] + list(f_df["date"])
        expected = [last_hist_price] + list(f_df["expected"])
        optimistic = [last_hist_price] + list(f_df["optimistic"])
        pessimistic = [last_hist_price] + list(f_df["pessimistic"])

        # Optimistic upper bound
        fig.add_trace(go.Scatter(
            x=dates,
            y=optimistic,
            mode="lines",
            line=dict(width=0),
            name="Optimistic (90th%)",
            showlegend=False,
            hoverinfo="skip"
        ))

        # Pessimistic lower bound with shaded confidence band
        fig.add_trace(go.Scatter(
            x=dates,
            y=pessimistic,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.15)",
            name="Confidence Interval",
            hoverinfo="skip"
        ))

        # Expected AI trajectory
        fig.add_trace(go.Scatter(
            x=dates,
            y=expected,
            mode="lines+markers",
            name="AI Forecast (Expected)",
            line=dict(color=AGRI_THEME["primary_green"], width=3, dash="solid"),
            marker=dict(size=6, color="#34d399"),
            hovertemplate="<b>Forecast Date</b>: %{x}<br><b>Expected Price</b>: ₹%{y:,.0f}/q<extra></extra>"
        ))

    fig.update_layout(
        title=f"<b>{crop} Price Forecast & Uncertainty Bands ({market} Mandi)</b>",
        paper_bgcolor=AGRI_THEME["paper_color"],
        plot_bgcolor=AGRI_THEME["bg_color"],
        font=dict(family=AGRI_THEME["font_family"], color=AGRI_THEME["font_color"]),
        xaxis=dict(showgrid=True, gridcolor=AGRI_THEME["grid_color"], title="Date"),
        yaxis=dict(showgrid=True, gridcolor=AGRI_THEME["grid_color"], title="Price (₹ per Quintal)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified"
    )
    return fig

def create_market_comparison_bar(comparisons: List[Dict[str, Any]], crop: str) -> go.Figure:
    """
    Renders comparative mandi prices alongside net realization after transport fees.
    """
    df = pd.DataFrame(comparisons)
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["market"],
        y=df["quoted_price"],
        name="Quoted Mandi Price",
        marker_color="#64748b",
        hovertemplate="<b>%{x}</b><br>Quoted: ₹%{y:,.0f}/q<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=df["market"],
        y=df["net_price_per_q"],
        name="Net Realization (After Logistics)",
        marker_color=AGRI_THEME["primary_green"],
        hovertemplate="<b>%{x}</b><br>Net: ₹%{y:,.0f}/q<extra></extra>"
    ))

    fig.update_layout(
        barmode="group",
        title=f"<b>Inter-Mandi Arbitrage: Quoted vs Net Realization for {crop}</b>",
        paper_bgcolor=AGRI_THEME["paper_color"],
        plot_bgcolor=AGRI_THEME["bg_color"],
        font=dict(family=AGRI_THEME["font_family"], color=AGRI_THEME["font_color"]),
        xaxis=dict(showgrid=False, title="Agricultural Mandi"),
        yaxis=dict(showgrid=True, gridcolor=AGRI_THEME["grid_color"], title="₹ per Quintal"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def create_profit_breakdown_waterfall(profit_data: Dict[str, Any]) -> go.Figure:
    """
    Waterfall chart of cultivation costs leading to Net Profit.
    """
    rev = profit_data["gross_revenue"]
    exp = profit_data["expenses_breakdown"]
    net_p = profit_data["net_profit"]

    labels = ["Gross Revenue", "Seeds", "Fertilizers", "Pesticides", "Labour", "Irrigation", "Transport & Logistics", "Mandi Cess", "Net Profit"]
    values = [
        rev,
        -exp.get("seeds", 0),
        -exp.get("fertilizers", 0),
        -exp.get("pesticides", 0),
        -exp.get("labour", 0),
        -exp.get("irrigation_water", 0),
        -exp.get("transportation", 0) - exp.get("storage", 0),
        -exp.get("mandi_cess", 0),
        net_p
    ]

    measures = ["absolute"] + ["relative"] * 7 + ["total"]

    fig = go.Figure(go.Waterfall(
        name="Financial Flow",
        orientation="v",
        measure=measures,
        x=labels,
        textposition="outside",
        text=[f"₹{abs(v):,.0f}" for v in values],
        y=values,
        connector={"line": {"color": "rgba(255,255,255,0.2)"}},
        decreasing={"marker": {"color": AGRI_THEME["danger_red"]}},
        increasing={"marker": {"color": AGRI_THEME["primary_green"]}},
        totals={"marker": {"color": "#38bdf8"}}
    ))

    fig.update_layout(
        title=f"<b>Farmer Financial P&L Waterfall ({profit_data['crop']} - {profit_data['quantity_quintals']} Quintals)</b>",
        paper_bgcolor=AGRI_THEME["paper_color"],
        plot_bgcolor=AGRI_THEME["bg_color"],
        font=dict(family=AGRI_THEME["font_family"], color=AGRI_THEME["font_color"]),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=AGRI_THEME["grid_color"], title="Amount (₹)"),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def create_weather_impact_chart(historical_df: pd.DataFrame) -> go.Figure:
    """Dual-axis chart showing daily rainfall against modal crop price."""
    df_tail = historical_df.tail(60).copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_tail["date"],
        y=df_tail["rainfall_mm"],
        name="Daily Rainfall (mm)",
        marker_color="rgba(56, 189, 248, 0.4)",
        yaxis="y2",
        hovertemplate="Rainfall: %{y:.1f} mm<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df_tail["date"],
        y=df_tail["modal_price"],
        name="Modal Price (₹/q)",
        mode="lines+markers",
        line=dict(color=AGRI_THEME["primary_green"], width=2.5),
        marker=dict(size=4),
        yaxis="y",
        hovertemplate="Price: ₹%{y:,.0f}/q<extra></extra>"
    ))

    fig.update_layout(
        title="<b>Rainfall Events vs Mandi Price Response (Last 60 Days)</b>",
        paper_bgcolor=AGRI_THEME["paper_color"],
        plot_bgcolor=AGRI_THEME["bg_color"],
        font=dict(family=AGRI_THEME["font_family"], color=AGRI_THEME["font_color"]),
        xaxis=dict(showgrid=True, gridcolor=AGRI_THEME["grid_color"]),
        yaxis=dict(title="Price (₹/q)", showgrid=True, gridcolor=AGRI_THEME["grid_color"]),
        yaxis2=dict(title="Rainfall (mm)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

