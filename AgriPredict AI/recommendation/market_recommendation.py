"""
Inter-Market Comparison & Smart Transportation Optimization Engine.
Evaluates price spreads across regional mandis, factors in freight and transit loss,
and identifies the highest net-yield market destination.
"""
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class MarketComparisonEngine:
    """
    Compares commodity prices across multiple mandis and optimizes logistics routing.
    """
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = str(PROJECT_ROOT / "config" / "settings.yaml")
        
        with open(config_path, "r") as f:
            self.cfg = yaml.safe_load(f)
            
        self.markets_info = self.cfg.get("markets", {})
        self.distances = self.cfg.get("inter_market_distances_km", {})

    def compare_markets(
        self,
        crop: str,
        origin_market: str,
        quantity_quintals: float,
        market_prices: Dict[str, float],
        diesel_cost_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates net realization for selling in origin vs transport to alternative mandis.
        """
        origin_price = market_prices.get(origin_market, 1800.0)
        origin_m_info = self.markets_info.get(origin_market, {"base_freight_per_km_tonne": 6.5})

        comparisons = []
        origin_dist_map = self.distances.get(origin_market, {})

        for mkt_name, mkt_price in market_prices.items():
            dist_km = origin_dist_map.get(mkt_name, 0)
            
            # Transport cost calculation
            # 1 tonne = 10 quintals
            tonnes = quantity_quintals / 10.0
            freight_rate_per_km_tonne = origin_m_info.get("base_freight_per_km_tonne", 6.5) * diesel_cost_multiplier
            
            if dist_km == 0:
                freight_total = 0.0
                loading_unloading = 0.0
                transit_loss_pct = 0.0
            else:
                freight_total = dist_km * freight_rate_per_km_tonne * tonnes
                # Flat loading/unloading and toll charge per tonne
                loading_unloading = 150.0 * tonnes
                # Transit loss / shrinkage (0.15% per 100km for perishables)
                transit_loss_pct = min(4.0, (dist_km / 100.0) * 0.20)

            total_logistics_cost = freight_total + loading_unloading
            logistics_per_q = total_logistics_cost / (quantity_quintals + 1e-4)

            # Effective yield after transit shrinkage
            effective_qty = quantity_quintals * (1.0 - (transit_loss_pct / 100.0))
            gross_revenue = effective_qty * mkt_price
            net_realization = gross_revenue - total_logistics_cost
            net_price_per_q = net_realization / (quantity_quintals + 1e-4)

            # Net gain over selling locally at origin market
            origin_gross = quantity_quintals * origin_price
            net_advantage = net_realization - origin_gross
            advantage_per_q = net_advantage / (quantity_quintals + 1e-4)

            comparisons.append({
                "market": mkt_name,
                "is_origin": (mkt_name == origin_market),
                "distance_km": dist_km,
                "quoted_price": round(mkt_price, 0),
                "logistics_total_cost": round(total_logistics_cost, 0),
                "logistics_cost_per_q": round(logistics_per_q, 1),
                "transit_loss_pct": round(transit_loss_pct, 1),
                "gross_revenue": round(gross_revenue, 0),
                "net_realization": round(net_realization, 0),
                "net_price_per_q": round(net_price_per_q, 0),
                "net_advantage_vs_origin": round(net_advantage, 0),
                "advantage_per_q": round(advantage_per_q, 0),
                "state": self.markets_info.get(mkt_name, {}).get("state", "India")
            })

        # Sort by highest net realization
        comparisons.sort(key=lambda c: c["net_realization"], reverse=True)
        best_market = comparisons[0]

        summary_msg = ""
        if best_market["market"] == origin_market:
            summary_msg = f"Sell locally at {origin_market}. Higher price in other mandis is outweighed by transit costs."
        else:
            summary_msg = (
                f"Transport to {best_market['market']} ({best_market['distance_km']} km away). "
                f"Net gain of +₹{best_market['net_advantage_vs_origin']:,.0f} (+₹{best_market['advantage_per_q']:,.0f}/q) "
                f"even after covering logistics fees."
            )

        return {
            "crop": crop,
            "origin_market": origin_market,
            "origin_price": round(origin_price, 0),
            "quantity_quintals": quantity_quintals,
            "best_market": best_market["market"],
            "best_net_gain": best_market["net_advantage_vs_origin"],
            "best_net_gain_per_q": best_market["advantage_per_q"],
            "summary_recommendation": summary_msg,
            "comparisons": comparisons
        }

