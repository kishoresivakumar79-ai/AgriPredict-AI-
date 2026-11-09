"""
UI Component: Metric Cards, Status Badges, and Alert Banners.
"""
import streamlit as st

def render_metric_card(
    title: str,
    value: str,
    subtext: str = "",
    delta: str = "",
    delta_color: str = "normal", # "normal", "inverse", "off"
    icon: str = "🌾"
):
    """Renders a styled metric card with delta indicator."""
    with st.container():
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 12px;
                padding: 16px 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.15);
                margin-bottom: 12px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">{title}</span>
                    <span style="font-size: 1.25rem;">{icon}</span>
                </div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #f8fafc; margin: 6px 0 2px 0;">{value}</div>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span style="font-size: 0.82rem; color: #64748b;">{subtext}</span>
                    <span style="font-size: 0.88rem; font-weight: 600; color: {'#10b981' if '+' in delta else ('#ef4444' if '-' in delta else '#38bdf8')};">{delta}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_recommendation_banner(
    action_headline: str,
    urgency: str = "Standard",
    risk_level: str = "Medium",
    confidence_score: int = 88,
    reasons: list = None
):
    """Renders a prominent AI Recommendation banner with color grading."""
    badge_color = "#10b981" if "Store" in action_headline else ("#3b82f6" if "Transport" in action_headline or "Switch" in action_headline else "#f59e0b")
    
    reasons_html = "".join([f"<li style='margin-bottom: 4px;'>{r}</li>" for r in (reasons or [])])

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 78, 59, 0.25));
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-left: 6px solid {badge_color};
            border-radius: 12px;
            padding: 20px 24px;
            margin: 15px 0 20px 0;
            box-shadow: 0 6px 20px rgba(0,0,0,0.25);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; color: #34d399; font-weight: 700;">AI Action Advisory</span>
                    <h3 style="margin: 4px 0 8px 0; color: #f8fafc; font-size: 1.4rem;">{action_headline}</h3>
                </div>
                <div style="display: flex; gap: 10px; margin-top: 5px;">
                    <span style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Confidence: {confidence_score}%</span>
                    <span style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Risk: {risk_level}</span>
                </div>
            </div>
            <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 12px 0;">
            <ul style="color: #cbd5e1; font-size: 0.92rem; padding-left: 20px; margin: 0;">
                {reasons_html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

