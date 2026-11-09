"""
AI Farmer Assistant Service ('Krishi Mitra' / Agricultural Advisor).
Answers farmers' natural-language questions regarding crop forecasts,
mandi arbitrage, storage decisions, and weather risks.
"""
import sys
import re
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.price_service import PriceService
from backend.services.recommendation_service import RecommendationService

class FarmerAssistant:
    """
    Conversational AI engine for farmer queries.
    """
    def __init__(self):
        self.price_service = PriceService()
        self.rec_service = RecommendationService()
        self.known_crops = ["Tomato", "Onion", "Potato", "Rice", "Maize"]
        self.known_markets = ["Salem", "Erode", "Coimbatore", "Namakkal", "Dindigul", "Nashik", "Pune"]

    def answer_query(self, user_question: str) -> Dict[str, Any]:
        """
        Processes farmer query and synthesizes data-backed advisory.
        """
        q = user_question.lower()

        # Detect Crop
        detected_crop = "Tomato" # default
        for c in self.known_crops:
            if c.lower() in q:
                detected_crop = c
                break

        # Detect Market
        detected_mkt = "Salem" # default
        for m in self.known_markets:
            if m.lower() in q:
                detected_mkt = m
                break

        # Detect Horizon
        horizon = 15
        if "next week" in q or "7 days" in q or "7 day" in q or "one week" in q:
            horizon = 7
        elif "month" in q or "30 days" in q or "30 day" in q:
            horizon = 30
        elif "15 days" in q or "two weeks" in q:
            horizon = 15

        # Query intent routing
        if any(w in q for w in ["store", "storage", "keep", "cold storage", "sell now or"]):
            # Storage / Sell vs Store Intent
            advisory = self.rec_service.get_full_farmer_advisory(detected_crop, detected_mkt, horizon_days=horizon)
            storage = advisory["storage_analysis"]
            best_strat = storage["optimal_strategy"]
            gain = storage["net_benefit_vs_immediate"]
            suitability = storage["suitability_note"]
            
            response = (
                f"🌾 **Storage Recommendation for {detected_crop} ({detected_mkt} Mandi)**:\n\n"
                f"• **Recommended Action**: **{best_strat}**\n"
                f"• **Current Market Rate**: ₹{storage['strategies'][0]['expected_price']:,.0f} per quintal\n"
                f"• **Net Financial Impact**: Projected gain of **+₹{gain:,.0f}** over immediate selling (factoring storage charges & spoilage).\n"
                f"• **Storage Suitability**: {suitability}.\n\n"
                f"💡 *Expert Tip*: Ensure proper sorting and moisture grading prior to loading into storage."
            )
            intent = "STORAGE_DECISION"

        elif any(w in q for w in ["which mandi", "which market", "best market", "compare", "where to sell", "where should i sell"]):
            # Market Arbitrage Intent
            all_prices = self.price_service.get_all_market_prices_latest(detected_crop)
            comp = self.rec_service.market_comp.compare_markets(
                crop=detected_crop,
                origin_market=detected_mkt,
                quantity_quintals=100.0,
                market_prices=all_prices
            )
            best_m = comp["best_market"]
            diff = comp["best_net_gain_per_q"]
            
            response = (
                f"🚛 **Mandi Price & Transport Arbitrage for {detected_crop}**:\n\n"
                f"• **Highest Net-Yield Market**: **{best_m} Mandi**\n"
                f"• **Origin ({detected_mkt}) Price**: ₹{comp['origin_price']:,.0f}/q\n"
                f"• **Net Profit Advantage**: **+₹{diff:,.0f} per quintal** (net after deducting transport fuel, loading, and transit loss).\n\n"
                f"📍 *Advice*: {comp['summary_recommendation']}"
            )
            intent = "MARKET_COMPARISON"

        elif any(w in q for w in ["rain", "rainfall", "weather", "drought", "flood", "temperature"]):
            # Weather Impact Intent
            advisory = self.rec_service.get_full_farmer_advisory(detected_crop, detected_mkt)
            curr_p = advisory["forecast"]["current_price"]
            w_res = self.rec_service.weather_sim.simulate_weather_shock(crop=detected_crop, base_price=curr_p, rainfall_anomaly_pct=40.0)
            
            response = (
                f"🌦️ **Weather Impact Analysis for {detected_crop}**:\n\n"
                f"• **Weather Sensitivity**: {detected_crop} has high vulnerability to rainfall saturation and root rot.\n"
                f"• **Supply Shock Impact**: A 40% excess rainfall event leads to ~{w_res['yield_damage_pct']}% regional harvest damage.\n"
                f"• **Price Dynamic**: Tightened arrivals push prices up from ₹{curr_p:,.0f} to estimated ₹{w_res['simulated_price']:,.0f} (+{w_res['price_increase_pct']}%).\n\n"
                f"💡 *Crop Protection*: Ensure furrow drainage in fields to avert water stagnation."
            )
            intent = "WEATHER_IMPACT"

        elif any(w in q for w in ["profit", "cost", "revenue", "break even", "expense"]):
            # Profit Calculation Intent
            from simulation.profit_simulator import FarmerProfitSimulator
            prof_sim = FarmerProfitSimulator()
            curr_p = self.price_service.get_price_forecast(detected_crop, detected_mkt)["current_price"]
            p_res = prof_sim.calculate_profit(crop=detected_crop, quantity_quintals=100.0, selling_price_per_q=curr_p)

            response = (
                f"💰 **Farmer Profitability Sheet for 100 Quintals of {detected_crop}**:\n\n"
                f"• **Selling Price**: ₹{curr_p:,.0f}/quintal\n"
                f"• **Total Estimated Revenue**: ₹{p_res['gross_revenue']:,.0f}\n"
                f"• **Total Production & Harvest Expenses**: ₹{p_res['total_expenses']:,.0f}\n"
                f"• **Net Estimated Profit**: **₹{p_res['net_profit']:,.0f}**\n"
                f"• **Break-Even Price**: ₹{p_res['break_even_price_per_q']:,.0f}/quintal\n"
                f"• **Return on Investment (ROI)**: **{p_res['roi_pct']:.1f}%** ({p_res['financial_health']})"
            )
            intent = "PROFIT_ESTIMATION"

        else:
            # Default: Price Prediction Intent
            fc = self.price_service.get_price_forecast(detected_crop, detected_mkt, horizon_days=horizon)
            p_chg = fc["price_change_pct"]
            direction = "increase 📈" if p_chg >= 0 else "decrease 📉"

            response = (
                f"🔮 **AI Price Prediction for {detected_crop} in {detected_mkt} Mandi**:\n\n"
                f"• **Current Spot Price**: ₹{fc['current_price']:,.0f} per quintal\n"
                f"• **Predicted Price in {horizon} Days**: **₹{fc['predicted_price']:,.0f} per quintal** ({direction} of {abs(p_chg):.1f}%)\n"
                f"• **Risk Confidence Range (90%)**:\n"
                f"   - 🟢 Optimistic Scenario: ₹{fc['optimistic_price']:,.0f}/q\n"
                f"   - 🔴 Pessimistic Scenario: ₹{fc['pessimistic_price']:,.0f}/q\n"
                f"• **AI Model**: {fc['model_used']}\n\n"
                f"💡 *Strategic Recommendation*: {'Consider holding crop in cold storage.' if p_chg > 10 else 'Good time to execute planned sale.'}"
            )
            intent = "PRICE_FORECAST"

        return {
            "question": user_question,
            "detected_crop": detected_crop,
            "detected_market": detected_mkt,
            "horizon_days": horizon,
            "intent": intent,
            "answer_markdown": response
        }

