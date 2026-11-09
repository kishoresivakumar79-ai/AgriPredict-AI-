"""
Supply and Demand Economic Simulation Engine.
Implements non-linear market equilibrium price elasticity:
P_new = P_base * ((D_new / D_base) / (S_new / S_base)) ^ epsilon
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class SupplyDemandSimulator:
    """
    Simulates agricultural market price equilibrium changes under supply and demand shocks.
    """
    # Crop price elasticity of demand / supply parameters
    DEFAULT_ELASTICITIES = {
        "Tomato": 0.65,
        "Onion": 0.55,
        "Potato": 0.45,
        "Rice": 0.35,
        "Maize": 0.40
    }

    def simulate(
        self,
        crop: str,
        base_price: float,
        base_supply_tonnes: float,
        new_supply_tonnes: float,
        base_demand_index: float = 100.0,
        new_demand_index: float = 100.0,
        custom_elasticity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes supply-demand equilibrium price calculation.
        """
        epsilon = custom_elasticity if custom_elasticity is not None else self.DEFAULT_ELASTICITIES.get(crop, 0.50)

        # Guard against zero or negative values
        s_base = max(1.0, float(base_supply_tonnes))
        s_new = max(1.0, float(new_supply_tonnes))
        d_base = max(1.0, float(base_demand_index))
        d_new = max(1.0, float(new_demand_index))

        demand_ratio = d_new / d_base
        supply_ratio = s_new / s_base

        # Economic equilibrium formulation
        market_pressure_ratio = demand_ratio / supply_ratio
        price_multiplier = market_pressure_ratio ** epsilon
        new_price = round(base_price * price_multiplier, 0)
        price_change_pct = round(((new_price - base_price) / base_price) * 100.0, 2)
        supply_change_pct = round(((s_new - s_base) / s_base) * 100.0, 1)
        demand_change_pct = round(((d_new - d_base) / d_base) * 100.0, 1)

        # Market condition categorization
        net_imbalance = demand_ratio - supply_ratio
        if net_imbalance > 0.15:
            market_state = "Deficit / Scarcity (Prices Surging)"
            status_color = "red"
        elif net_imbalance < -0.15:
            market_state = "Surplus / Market Glut (Prices Crashing)"
            status_color = "green"
        else:
            market_state = "Stable Market Equilibrium"
            status_color = "blue"

        return {
            "crop": crop,
            "base_price": round(base_price, 0),
            "new_simulated_price": round(new_price, 0),
            "price_difference": round(new_price - base_price, 0),
            "price_change_pct": price_change_pct,
            "base_supply_tonnes": s_base,
            "new_supply_tonnes": s_new,
            "supply_change_pct": supply_change_pct,
            "base_demand_index": d_base,
            "new_demand_index": d_new,
            "demand_change_pct": demand_change_pct,
            "elasticity_epsilon": epsilon,
            "market_state": market_state,
            "status_color": status_color
        }

