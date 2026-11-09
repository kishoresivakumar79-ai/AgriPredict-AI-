"""
Farmer Profit and Cultivation Economics Simulator.
Calculates production expenses (seed, fertilizer, pesticide, labour, irrigation),
logistics & storage outlays, gross revenues, and net farm gate profits.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class FarmerProfitSimulator:
    """
    Computes agricultural profit margins, break-even price, and return on investment (ROI).
    """
    DEFAULT_CULTIVATION_BREAKDOWN = {
        "Tomato": {
            "seeds_per_acre": 7500.0,
            "fertilizer_per_acre": 14000.0,
            "pesticides_per_acre": 11000.0,
            "labour_per_acre": 22000.0,
            "irrigation_per_acre": 6500.0,
            "avg_yield_quintals_acre": 105.0
        },
        "Onion": {
            "seeds_per_acre": 6000.0,
            "fertilizer_per_acre": 12000.0,
            "pesticides_per_acre": 8500.0,
            "labour_per_acre": 19000.0,
            "irrigation_per_acre": 5500.0,
            "avg_yield_quintals_acre": 90.0
        },
        "Potato": {
            "seeds_per_acre": 18000.0,
            "fertilizer_per_acre": 13500.0,
            "pesticides_per_acre": 7500.0,
            "labour_per_acre": 16000.0,
            "irrigation_per_acre": 6000.0,
            "avg_yield_quintals_acre": 120.0
        },
        "Rice": {
            "seeds_per_acre": 3500.0,
            "fertilizer_per_acre": 9500.0,
            "pesticides_per_acre": 5000.0,
            "labour_per_acre": 18000.0,
            "irrigation_per_acre": 7000.0,
            "avg_yield_quintals_acre": 45.0
        },
        "Maize": {
            "seeds_per_acre": 3200.0,
            "fertilizer_per_acre": 8500.0,
            "pesticides_per_acre": 4500.0,
            "labour_per_acre": 15000.0,
            "irrigation_per_acre": 5000.0,
            "avg_yield_quintals_acre": 50.0
        }
    }

    def calculate_profit(
        self,
        crop: str,
        quantity_quintals: float,
        selling_price_per_q: float,
        acres_cultivated: Optional[float] = None,
        custom_seed_cost: Optional[float] = None,
        custom_fertilizer_cost: Optional[float] = None,
        custom_pesticide_cost: Optional[float] = None,
        custom_labour_cost: Optional[float] = None,
        custom_irrigation_cost: Optional[float] = None,
        transport_cost_total: float = 0.0,
        storage_cost_total: float = 0.0,
        mandi_cess_pct: float = 1.5
    ) -> Dict[str, Any]:
        """
        Calculates full farm profit sheet.
        """
        defaults = self.DEFAULT_CULTIVATION_BREAKDOWN.get(crop, self.DEFAULT_CULTIVATION_BREAKDOWN["Tomato"])
        
        # Estimate acres if not explicitly provided
        if acres_cultivated is None or acres_cultivated <= 0:
            acres = max(0.5, quantity_quintals / defaults["avg_yield_quintals_acre"])
        else:
            acres = acres_cultivated

        seed_cost = custom_seed_cost if custom_seed_cost is not None else (defaults["seeds_per_acre"] * acres)
        fert_cost = custom_fertilizer_cost if custom_fertilizer_cost is not None else (defaults["fertilizer_per_acre"] * acres)
        pest_cost = custom_pesticide_cost if custom_pesticide_cost is not None else (defaults["pesticides_per_acre"] * acres)
        labour_cost = custom_labour_cost if custom_labour_cost is not None else (defaults["labour_per_acre"] * acres)
        water_cost = custom_irrigation_cost if custom_irrigation_cost is not None else (defaults["irrigation_per_acre"] * acres)

        total_production_cost = seed_cost + fert_cost + pest_cost + labour_cost + water_cost

        # Revenue
        gross_revenue = quantity_quintals * selling_price_per_q
        mandi_cess_amount = gross_revenue * (mandi_cess_pct / 100.0)

        # Total expenses
        total_expenses = (
            total_production_cost 
            + transport_cost_total 
            + storage_cost_total 
            + mandi_cess_amount
        )

        net_profit = gross_revenue - total_expenses
        profit_margin_pct = (net_profit / (gross_revenue + 1e-4)) * 100.0
        roi_pct = (net_profit / (total_expenses + 1e-4)) * 100.0
        cost_per_quintal = total_expenses / (quantity_quintals + 1e-4)
        break_even_price = cost_per_quintal

        return {
            "crop": crop,
            "quantity_quintals": round(quantity_quintals, 1),
            "acres_cultivated": round(acres, 2),
            "selling_price_per_q": round(selling_price_per_q, 0),
            "gross_revenue": round(gross_revenue, 0),
            "expenses_breakdown": {
                "seeds": round(seed_cost, 0),
                "fertilizers": round(fert_cost, 0),
                "pesticides": round(pest_cost, 0),
                "labour": round(labour_cost, 0),
                "irrigation_water": round(water_cost, 0),
                "transportation": round(transport_cost_total, 0),
                "storage": round(storage_cost_total, 0),
                "mandi_cess": round(mandi_cess_amount, 0),
            },
            "total_production_cost": round(total_production_cost, 0),
            "total_expenses": round(total_expenses, 0),
            "net_profit": round(net_profit, 0),
            "profit_margin_pct": round(profit_margin_pct, 2),
            "roi_pct": round(roi_pct, 2),
            "break_even_price_per_q": round(break_even_price, 0),
            "profit_per_quintal": round(selling_price_per_q - break_even_price, 0),
            "profit_per_acre": round(net_profit / acres, 0),
            "financial_health": "Highly Profitable" if roi_pct > 40 else ("Profitable" if roi_pct > 0 else "Operating at Loss")
        }

