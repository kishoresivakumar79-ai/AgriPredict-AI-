"""
Main Dashboard Orchestrator.
Coordinates the sidebar controls and routes to pages via intuitive navigation tabs.
Supports deep-linking query parameters (?view=...) for direct page access and automated capture.
"""
import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.components.sidebar import render_sidebar
from frontend.pages.home import render_home_page
from frontend.pages.price_prediction import render_price_prediction_page
from frontend.pages.market_analysis import render_market_analysis_page
from frontend.pages.weather_analysis import render_weather_analysis_page
from frontend.pages.supply_demand import render_supply_demand_page
from frontend.pages.profit_calculator import render_profit_calculator_page
from frontend.pages.scenario_simulator import render_scenario_simulator_page
from frontend.pages.assistant_and_reports import render_assistant_and_reports_page

def render_dashboard():
    """Renders main application layout with header, navigation, and page content."""
    # Render persistent sidebar controls
    settings = render_sidebar()

    # Check for direct view query parameter (useful for routing & automated screenshot capture)
    active_view = st.query_params.get("view", None)
    if active_view == "overview":
        render_home_page(settings)
        return
    elif active_view == "price_prediction":
        render_price_prediction_page(settings)
        return
    elif active_view == "market_analysis":
        render_market_analysis_page(settings)
        return
    elif active_view == "weather_analysis":
        render_weather_analysis_page(settings)
        return
    elif active_view == "supply_demand":
        render_supply_demand_page(settings)
        return
    elif active_view == "profit_calculator":
        render_profit_calculator_page(settings)
        return
    elif active_view == "scenario_simulator":
        render_scenario_simulator_page(settings)
        return
    elif active_view == "assistant_and_reports":
        render_assistant_and_reports_page(settings)
        return

    # Default: Top Navigation Tabs
    tabs = st.tabs([
        "🌾 Overview",
        "🔮 Price Prediction",
        "🚛 Market Comparison",
        "🌦️ Weather Impact",
        "⚖️ Supply & Demand",
        "💰 Profit & Storage",
        "🧪 What-If & Digital Twin",
        "🤖 AI Assistant & Reports"
    ])

    with tabs[0]:
        render_home_page(settings)

    with tabs[1]:
        render_price_prediction_page(settings)

    with tabs[2]:
        render_market_analysis_page(settings)

    with tabs[3]:
        render_weather_analysis_page(settings)

    with tabs[4]:
        render_supply_demand_page(settings)

    with tabs[5]:
        render_profit_calculator_page(settings)

    with tabs[6]:
        render_scenario_simulator_page(settings)

    with tabs[7]:
        render_assistant_and_reports_page(settings)
