"""
Streamlit Application Entry Point for AgriPredict AI.
Configures page layout, custom aesthetic CSS styling, and mounts main dashboard.
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Streamlit Page Config
st.set_page_config(
    page_title="AgriPredict AI — Market & Price Prediction Simulator",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Aesthetic Agri-Emerald CSS Styling
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Agri Emerald Accents */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(255, 255, 255, 0.03);
            padding: 8px 12px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 20px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 42px;
            border-radius: 8px;
            padding: 0 16px;
            font-size: 0.9rem;
            font-weight: 500;
            color: #94a3b8;
            border: none;
        }

        .stTabs [aria-selected="true"] {
            background-color: rgba(16, 185, 129, 0.18) !important;
            color: #34d399 !important;
            font-weight: 700;
            border: 1px solid rgba(16, 185, 129, 0.4) !important;
        }

        /* Metric card styling */
        div[data-testid="metric-container"] {
            background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
            border: 1px solid rgba(255,255,255,0.1);
            padding: 14px 18px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }

        /* Custom Scrollbars */
        ::-webkit-scrollbar {
            width: 7px;
            height: 7px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.1);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.15);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(16, 185, 129, 0.5);
        }
    </style>
    """,
    unsafe_allow_html=True
)

from frontend.dashboard import render_dashboard

if __name__ == "__main__":
    render_dashboard()

