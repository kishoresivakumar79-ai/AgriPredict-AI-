"""
Page: AI Farmer Assistant ('Krishi Mitra') & Analytical Reports Generator.
Provides interactive conversational Q&A and instant downloadable advisory reports.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any

from backend.services.assistant_service import FarmerAssistant
from backend.services.recommendation_service import RecommendationService
from backend.services.price_service import PriceService

def render_assistant_and_reports_page(settings: Dict[str, Any]):
    crop = settings["crop"]
    mandi = settings["mandi"]
    horizon = settings["horizon"]
    quantity = settings["quantity"]

    assistant = FarmerAssistant()
    rec_service = RecommendationService()
    price_service = PriceService()

    tab_chat, tab_reports = st.tabs(["🤖 Krishi Mitra (AI Assistant)", "📄 Export Analytical Reports"])

    with tab_chat:
        st.markdown("### 🌾 Krishi Mitra — Your AI Agricultural Advisor")
        st.write("Ask any question regarding crop price forecasts, storage decisions, or mandi transport arbitrage.")

        # Quick Prompt Chips
        st.markdown("**Quick Inquiries:**")
        chip_col1, chip_col2, chip_col3 = st.columns(3)
        with chip_col1:
            q1 = st.button(f"🔮 What will {crop} price be in {mandi} next week?")
        with chip_col2:
            q2 = st.button(f"❄️ Should I store my {crop} or sell now?")
        with chip_col3:
            q3 = st.button(f"🚛 Which mandi pays the highest for {crop}?")

        user_input = st.text_input("Ask a question to Krishi Mitra:", placeholder=f"e.g. Will tomato prices increase next week in Salem?")

        active_query = None
        if q1:
            active_query = f"What will {crop} price be in {mandi} next week?"
        elif q2:
            active_query = f"Should I store my {crop} or sell now in {mandi}?"
        elif q3:
            active_query = f"Which mandi pays the highest price for {crop} starting from {mandi}?"
        elif user_input:
            active_query = user_input

        if active_query:
            with st.spinner("Krishi Mitra is analyzing market data and weather models..."):
                res = assistant.answer_query(active_query)
                st.markdown("---")
                st.markdown(res["answer_markdown"])

    with tab_reports:
        st.markdown("### 📄 Comprehensive Market Advisory Report")
        st.write("Generate and download standardized agricultural intelligence briefs.")

        advisory = rec_service.get_full_farmer_advisory(
            crop=crop,
            current_market=mandi,
            quantity_quintals=quantity,
            horizon_days=horizon
        )

        fc = advisory["forecast"]
        dec = advisory["decision"]
        stor = advisory["storage_analysis"]
        mkt = advisory["market_comparison"]

        report_md = f"""# AgriPredict AI — Agricultural Market Intelligence Report
**Generated for**: Farmer / Market Participant
**Date**: {fc.get('latest_record_date', 'Today')}
**Crop**: {crop} | **Current Mandi**: {mandi} | **Quantity**: {quantity:,.0f} Quintals

---
### 1. Executive Price Summary
- **Current Spot Price**: ₹{fc['current_price']:,.0f} per quintal
- **AI Predicted Price ({horizon} Days)**: ₹{fc['predicted_price']:,.0f} per quintal ({fc['price_change_pct']:+.1f}%)
- **Optimistic Scenario (90th%)**: ₹{fc['optimistic_price']:,.0f} / q
- **Pessimistic Scenario (10th%)**: ₹{fc['pessimistic_price']:,.0f} / q
- **Selected Model**: {fc['model_used']}

---
### 2. AI Decision Advisory
- **Primary Recommendation**: {dec['headline']}
- **Action Urgency**: {dec['urgency']}
- **Risk Level**: {dec['risk_level']}
- **Confidence Rating**: {dec['confidence_score_pct']}%

**Key Strategic Reasons:**
{chr(10).join(['- ' + r for r in dec['reasons']])}

**Recommended Action Steps:**
{chr(10).join([f'{i}. {s}' for i, s in enumerate(dec['action_steps'], 1)])}

---
### 3. Storage vs Immediate Sale Analysis
- **Optimal Holding Strategy**: {stor['optimal_strategy']}
- **Net Gain vs Immediate Selling**: ₹{stor['net_benefit_vs_immediate']:,.0f}
- **Storage Type**: {stor['storage_type']}

---
### 4. Regional Mandi Arbitrage
- **Best Alternative Mandi**: {mkt['best_market']}
- **Net Transport Arbitrage Advantage**: +₹{mkt['best_net_gain_per_q']:,.0f} per quintal
- **Summary**: {mkt['summary_recommendation']}

---
*Disclaimer: AI predictions are based on empirical historical models and meteorological scenarios. Market participants should verify local trading regulations.*
"""

        st.download_button(
            label="📥 Download Advisory Report (Markdown)",
            data=report_md,
            file_name=f"AgriPredict_Report_{crop}_{mandi}.md",
            mime="text/markdown"
        )

        st.markdown("#### Report Preview")
        st.markdown(report_md)

