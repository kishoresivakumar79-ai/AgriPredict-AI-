"""
AI Decision and Farmer Advisory Recommendation Engine.
Synthesizes machine learning price forecasts, storage cost trade-offs,
logistics arbitrage, and weather risks into definitive agricultural decisions.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class AgriDecisionEngine:
    """
    Intelligent recommendation generator for farmers and agribusinesses.
    """
    def generate_recommendation(
        self,
        crop: str,
        current_market: str,
        current_price: float,
        predicted_price_15d: float,
        storage_analysis: Optional[Dict[str, Any]] = None,
        market_comparison: Optional[Dict[str, Any]] = None,
        weather_analysis: Optional[Dict[str, Any]] = None,
        quantity_quintals: float = 100.0
    ) -> Dict[str, Any]:
        """
        Evaluates multi-criteria conditions to output clear selling advice.
        """
        price_trend_pct = ((predicted_price_15d - current_price) / (current_price + 1e-4)) * 100.0
        
        reasons = []
        action_steps = []
        action = "SELL_NOW"
        urgency = "Standard"
        risk_level = "Medium"
        confidence_pct = 85

        # 1. Evaluate Storage Opportunity
        storage_optimal_days = 0
        storage_net_gain = 0.0
        if storage_analysis:
            storage_optimal_days = storage_analysis.get("optimal_days", 0)
            storage_net_gain = storage_analysis.get("net_benefit_vs_immediate", 0.0)

        # 2. Evaluate Mandi Arbitrage
        best_alt_mandi = current_market
        alt_mandi_gain = 0.0
        if market_comparison:
            best_alt_mandi = market_comparison.get("best_market", current_market)
            alt_mandi_gain = market_comparison.get("best_net_gain", 0.0)

        # 3. Decision Logic Flow
        if price_trend_pct > 12.0 and storage_optimal_days > 0 and storage_net_gain > 5000:
            action = "STORE_AND_SELL_LATER"
            urgency = "Moderate"
            risk_level = "Low"
            confidence_pct = 90
            reasons.append(f"AI models forecast a +{price_trend_pct:.1f}% price rally over the next 15 days (₹{current_price:,.0f} -> ₹{predicted_price_15d:,.0f}/q).")
            reasons.append(f"Holding for {storage_optimal_days} days yields an estimated net gain of ₹{storage_net_gain:,.0f} after deducting storage and spoilage costs.")
            action_steps.append(f"Deposit produce into certified cold storage warehouse at {current_market} or nearby hub.")
            action_steps.append(f"Monitor market arrival volumes around Day {storage_optimal_days - 2} to execute sale near peak price.")

        elif alt_mandi_gain > 7500 and best_alt_mandi != current_market:
            action = "SWITCH_MANDI"
            urgency = "High"
            risk_level = "Medium"
            confidence_pct = 88
            reasons.append(f"Quoted prices in {best_alt_mandi} offer significant premium over {current_market}.")
            reasons.append(f"Net arbitrage gain is +₹{alt_mandi_gain:,.0f} after deducting truck freight, tolls, and transit loss.")
            action_steps.append(f"Book transport freight to {best_alt_mandi} terminal market.")
            action_steps.append(f"Dispatch harvest early morning to target prime wholesale bidding window.")

        elif price_trend_pct < -8.0:
            action = "SELL_IMMEDIATELY"
            urgency = "Immediate"
            risk_level = "High"
            confidence_pct = 92
            reasons.append(f"Prices are projected to fall by {abs(price_trend_pct):.1f}% due to rising market arrivals and seasonal supply flush.")
            reasons.append("Holding produce risks both price depreciation and storage expense attrition.")
            action_steps.append(f"Liquidate full harvest in {current_market} mandi today.")
            action_steps.append("Avoid cold storage fees as projected prices will not cover holding costs.")

        elif price_trend_pct >= -8.0 and price_trend_pct <= 12.0:
            if crop in ["Tomato"]:
                action = "SELL_NOW_HIGH_PERISHABILITY"
                urgency = "High"
                risk_level = "High"
                confidence_pct = 82
                reasons.append(f"Tomato is highly perishable with ~3-4% daily ambient degradation.")
                reasons.append(f"Modest projected price move (+{price_trend_pct:.1f}%) does not justify post-harvest risks.")
                action_steps.append(f"Sell locally at {current_market} to minimize physical spoilage.")
            else:
                action = "SPLIT_SALE_HEDGE"
                urgency = "Standard"
                risk_level = "Low"
                confidence_pct = 85
                reasons.append("Market is in near-equilibrium with moderate volatility.")
                reasons.append("Staggered selling provides risk hedge against unexpected demand shifts.")
                action_steps.append("Sell 50% of harvest immediately to recover operational cultivation expenses.")
                action_steps.append("Store remaining 50% for 15-20 days to capture potential upside surges.")

        # Weather alerts integration
        if weather_analysis and weather_analysis.get("weather_risk_level") == "High":
            reasons.append(f"Alert: Weather shock expected ({weather_analysis.get('yield_damage_pct', 0)}% regional damage), which may further constrict supply.")

        action_labels = {
            "STORE_AND_SELL_LATER": "Store Produce (Sell Later)",
            "SWITCH_MANDI": f"Transport to {best_alt_mandi} Mandi",
            "SELL_IMMEDIATELY": "Sell Immediately at Current Mandi",
            "SELL_NOW_HIGH_PERISHABILITY": "Sell Immediately (Perishable Risk)",
            "SPLIT_SALE_HEDGE": "Split Selling Strategy (50% Now / 50% Later)"
        }

        return {
            "crop": crop,
            "market": current_market,
            "recommended_action": action,
            "headline": action_labels.get(action, "Sell Immediately"),
            "urgency": urgency,
            "risk_level": risk_level,
            "confidence_score_pct": confidence_pct,
            "current_price": round(current_price, 0),
            "predicted_price_15d": round(predicted_price_15d, 0),
            "price_trend_pct": round(price_trend_pct, 2),
            "reasons": reasons,
            "action_steps": action_steps,
            "best_market_destination": best_alt_mandi,
            "storage_recommended_days": storage_optimal_days
        }

