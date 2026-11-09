"""
Storage Decision Simulator.
Evaluates the trade-offs between immediate sale vs holding in ambient or cold storage
over 7, 15, and 30-day horizons factoring storage fees, physiological spoilage loss,
and price appreciation/depreciation.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class StorageSimulator:
    """
    Simulates storage economics and advises on optimal holding duration.
    """
    CROP_STORAGE_PROFILES = {
        "Tomato": {
            "ambient_cost_day": 1.2,
            "cold_cost_day": 4.5,
            "ambient_spoilage_pct_day": 3.5,
            "cold_spoilage_pct_day": 0.5,
            "max_ambient_days": 7,
            "max_cold_days": 25,
            "storage_suitability": "Cold Storage Only (High Perishability)"
        },
        "Onion": {
            "ambient_cost_day": 0.8,
            "cold_cost_day": 3.2,
            "ambient_spoilage_pct_day": 1.2,
            "cold_spoilage_pct_day": 0.25,
            "max_ambient_days": 45,
            "max_cold_days": 120,
            "storage_suitability": "Well-Ventilated or Cold Storage"
        },
        "Potato": {
            "ambient_cost_day": 0.6,
            "cold_cost_day": 2.8,
            "ambient_spoilage_pct_day": 0.8,
            "cold_spoilage_pct_day": 0.12,
            "max_ambient_days": 40,
            "max_cold_days": 180,
            "storage_suitability": "Excellent Cold Storage Candidate"
        },
        "Rice": {
            "ambient_cost_day": 0.4,
            "cold_cost_day": 1.5,
            "ambient_spoilage_pct_day": 0.05,
            "cold_spoilage_pct_day": 0.01,
            "max_ambient_days": 365,
            "max_cold_days": 730,
            "storage_suitability": "Warehouse Dry Storage"
        },
        "Maize": {
            "ambient_cost_day": 0.45,
            "cold_cost_day": 1.6,
            "ambient_spoilage_pct_day": 0.08,
            "cold_spoilage_pct_day": 0.015,
            "max_ambient_days": 240,
            "max_cold_days": 400,
            "storage_suitability": "Warehouse Dry Storage"
        }
    }

    def simulate_strategies(
        self,
        crop: str,
        quantity_quintals: float,
        current_price: float,
        price_7d: float,
        price_15d: float,
        price_30d: float,
        use_cold_storage: bool = True
    ) -> Dict[str, Any]:
        """
        Compares immediate sale against 7, 15, and 30 day holding strategies.
        """
        profile = self.CROP_STORAGE_PROFILES.get(
            crop,
            {
                "ambient_cost_day": 1.0,
                "cold_cost_day": 3.5,
                "ambient_spoilage_pct_day": 1.5,
                "cold_spoilage_pct_day": 0.3,
                "max_ambient_days": 15,
                "max_cold_days": 60,
                "storage_suitability": "Standard Storage"
            }
        )

        cost_day = profile["cold_cost_day"] if use_cold_storage else profile["ambient_cost_day"]
        spoilage_rate = profile["cold_spoilage_pct_day"] if use_cold_storage else profile["ambient_spoilage_pct_day"]

        # Strategy 0: Immediate Sale
        imm_revenue = quantity_quintals * current_price
        imm_net = imm_revenue # storage cost is 0

        strategies = [
            {
                "strategy": "Immediate Sale",
                "days": 0,
                "expected_price": round(current_price, 0),
                "storage_cost": 0.0,
                "spoilage_pct": 0.0,
                "spoilage_loss_quintals": 0.0,
                "effective_quantity": round(quantity_quintals, 1),
                "gross_revenue": round(imm_revenue, 0),
                "net_realization": round(imm_net, 0),
                "net_gain_vs_immediate": 0.0,
                "gain_per_quintal": 0.0
            }
        ]

        horizons = [(7, price_7d), (15, price_15d), (30, price_30d)]

        for days, exp_p in horizons:
            total_storage_cost = quantity_quintals * cost_day * days
            spoil_pct = min(40.0, spoilage_rate * days)
            spoil_qty = quantity_quintals * (spoil_pct / 100.0)
            eff_qty = max(0.0, quantity_quintals - spoil_qty)
            gross_rev = eff_qty * exp_p
            net_real = gross_rev - total_storage_cost
            net_gain = net_real - imm_net
            gain_per_q = net_gain / (quantity_quintals + 1e-4)

            strategies.append({
                "strategy": f"Store for {days} Days",
                "days": days,
                "expected_price": round(exp_p, 0),
                "storage_cost": round(total_storage_cost, 0),
                "spoilage_pct": round(spoil_pct, 1),
                "spoilage_loss_quintals": round(spoil_qty, 1),
                "effective_quantity": round(eff_qty, 1),
                "gross_revenue": round(gross_rev, 0),
                "net_realization": round(net_real, 0),
                "net_gain_vs_immediate": round(net_gain, 0),
                "gain_per_quintal": round(gain_per_q, 1)
            })

        # Identify best strategy by net realization
        best = max(strategies, key=lambda s: s["net_realization"])

        recommendation = ""
        if best["days"] == 0:
            recommendation = (
                f"Sell immediately at current market rate ₹{current_price:,.0f}/q. "
                f"Holding risks price drop or storage costs outweighing price gains."
            )
        else:
            recommendation = (
                f"Optimal Strategy: {best['strategy']} in {'Cold' if use_cold_storage else 'Ambient'} storage. "
                f"Projected net gain of ₹{best['net_gain_vs_immediate']:,.0f} (+₹{best['gain_per_quintal']:,.0f}/quintal) "
                f"after accounting for storage fees and spoilage."
            )

        return {
            "crop": crop,
            "quantity_quintals": quantity_quintals,
            "storage_type": "Cold Storage" if use_cold_storage else "Ambient Storage",
            "daily_storage_fee_per_q": cost_day,
            "daily_spoilage_rate_pct": spoilage_rate,
            "strategies": strategies,
            "optimal_strategy": best["strategy"],
            "optimal_days": best["days"],
            "max_net_realization": best["net_realization"],
            "net_benefit_vs_immediate": best["net_gain_vs_immediate"],
            "recommendation": recommendation,
            "suitability_note": profile["storage_suitability"]
        }

