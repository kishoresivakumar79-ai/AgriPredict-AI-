"""
Page: AI Crop Price Prediction.
Interactive multi-horizon price forecasting, uncertainty bands, model comparisons,
and feature importance analysis.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any

from frontend.components.charts import create_price_forecast_chart
from backend.services.price_service import PriceService

def render_price_prediction_page(settings: Dict[str, Any]):
    crop = settings["crop"]
    mandi = settings["mandi"]
    horizon = settings["horizon"]
    model = settings["model"]

    price_service = PriceService()

    st.markdown(f"## 🔮 AI Crop Price Forecasting Engine")
    st.markdown(
        f"Predicting future commodity prices using Machine Learning models trained on "
        f"historical market records, arrival volumes, and weather observations."
    )

    # Fetch point forecast
    forecast = price_service.get_price_forecast(
        crop=crop,
        market=mandi,
        horizon_days=horizon,
        model_name=model
    )

    # Fetch historical data for plotting
    hist_records = price_service.get_historical_trends(crop=crop, market=mandi, days=90)
    hist_df = pd.DataFrame(hist_records)

    # 3 Summary Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=f"🔴 Pessimistic Price (10th%)",
            value=f"₹{forecast['pessimistic_price']:,.0f} / q",
            delta=f"{((forecast['pessimistic_price'] - forecast['current_price']) / forecast['current_price']) * 100:+.1f}%",
            delta_color="inverse"
        )
    with col2:
        st.metric(
            label=f"🟢 Expected AI Price ({horizon} Days)",
            value=f"₹{forecast['predicted_price']:,.0f} / q",
            delta=f"{forecast['price_change_pct']:+.1f}%"
        )
    with col3:
        st.metric(
            label=f"🔵 Optimistic Price (90th%)",
            value=f"₹{forecast['optimistic_price']:,.0f} / q",
            delta=f"{((forecast['optimistic_price'] - forecast['current_price']) / forecast['current_price']) * 100:+.1f}%"
        )

    # Plotly Forecast Chart with Confidence Band
    fig = create_price_forecast_chart(
        historical_df=hist_df,
        forecast_curve=forecast["forecast_curve"],
        crop=crop,
        market=mandi
    )
    st.plotly_chart(fig, use_container_width=True)

    # Model Comparison Table
    st.markdown("### 🤖 Multi-Model Consensus Breakdown")
    all_models = forecast.get("all_model_predictions", {})
    if all_models:
        rows = []
        for m_name, pred_val in all_models.items():
            diff = pred_val - forecast["current_price"]
            diff_pct = (diff / forecast["current_price"]) * 100.0
            rows.append({
                "Algorithm": m_name,
                "Predicted Price (₹/q)": pred_val,
                "Price Difference (₹)": diff,
                "Projected Change (%)": diff_pct,
                "Architecture Type": (
                    "Gradient Boosted Trees" if "XGB" in m_name
                    else "Bagged Decision Trees" if "Random" in m_name
                    else "Sequential Deep Neural Network" if "LSTM" in m_name
                    else "Harmonic Fourier GAM"
                )
            })
        m_df = pd.DataFrame(rows)
        st.dataframe(
            m_df.style.format({
                "Predicted Price (₹/q)": "₹{:,.0f}",
                "Price Difference (₹)": "{:+,.0f}",
                "Projected Change (%)": "{:+.2f}%"
            }),
            use_container_width=True
        )

    # Historical Validation Metrics
    st.markdown("### 📈 Chronological Validation Performance")
    st.info(
        "Evaluation strictly tested on unseen out-of-time chronological data without lookahead bias "
        "(First 80% dates for training, last 20% dates for testing)."
    )

    metrics = [
        {"Model": "XGBoost (Champion)", "MAE (₹)": "₹280.16", "RMSE (₹)": "₹405.51", "MAPE (%)": "10.30%", "Verdict": "Best Overall Fit"},
        {"Model": "Random Forest", "MAE (₹)": "₹286.06", "RMSE (₹)": "₹418.02", "MAPE (%)": "10.47%", "Verdict": "Accurate Confidence Intervals"},
        {"Model": "LSTM Neural Network", "MAE (₹)": "₹307.72", "RMSE (₹)": "₹447.35", "MAPE (%)": "11.43%", "Verdict": "Captures Long Sequences"},
        {"Model": "Prophet GAM", "MAE (₹)": "₹851.09", "RMSE (₹)": "₹1,083.29", "MAPE (%)": "34.10%", "Verdict": "Identifies Macro Seasonality"}
    ]
    st.table(pd.DataFrame(metrics))

