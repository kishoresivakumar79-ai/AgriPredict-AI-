"""
UI Component: Global Sidebar Controls, Commodity Selectors, and User Persona Switcher.
"""
import streamlit as st
from typing import Dict, Any, Tuple

def render_sidebar() -> Dict[str, Any]:
    """Renders persistent global controls in Streamlit sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <span style="font-size: 2rem;">🌾</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.3rem; color: #10b981; font-weight: 800;">AgriPredict AI</h2>
                    <span style="font-size: 0.75rem; color: #94a3b8;">Agricultural Market Simulator</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 1. User Role Persona
        role = st.selectbox(
            "👤 User Persona / Role",
            options=["Farmer / Producer", "Market Trader / Aggregator", "Agri Policy Analyst (Admin)"],
            index=0
        )

        st.markdown("---")
        st.markdown("#### 📍 Commodity & Location")

        crops = ["Tomato", "Onion", "Potato", "Rice", "Maize"]
        selected_crop = st.selectbox("🌱 Select Crop", crops, index=0)

        mandis = ["Salem", "Erode", "Coimbatore", "Namakkal", "Dindigul", "Nashik", "Pune"]
        selected_mandi = st.selectbox("🏢 Agricultural Mandi", mandis, index=0)

        st.markdown("#### ⏱️ Prediction Settings")
        horizon = st.radio("Forecast Horizon", options=[7, 15, 30], index=1, format_func=lambda x: f"{x} Days Ahead")

        models = ["Ensemble", "XGBoost", "RandomForest", "LSTM", "Prophet"]
        selected_model = st.selectbox("🤖 ML Model", models, index=0)

        st.markdown("---")
        # Farmer specific parameter
        quantity = 100.0
        if "Farmer" in role:
            quantity = st.number_input("📦 Harvest Quantity (Quintals)", min_value=10.0, max_value=5000.0, value=100.0, step=10.0)

        st.markdown(
            """
            <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 10px; margin-top: 20px; font-size: 0.75rem; color: #64748b;">
                <b>AgriPredict Engine v2.5</b><br>
                Data source: Agmarknet & IMD Station Records<br>
                Validation: Chronological Split (No Lookahead Bias)
            </div>
            """,
            unsafe_allow_html=True
        )

    return {
        "role": role,
        "crop": selected_crop,
        "mandi": selected_mandi,
        "horizon": horizon,
        "model": selected_model,
        "quantity": quantity
    }

