"""
What-If Market Scenario & Multi-Agent Agricultural Digital Twin Simulator.
Enables parametric simulation of extreme macro events (bumper harvests, export bans,
diesel price surges, drought shocks) and simulates multi-stakeholder market transactions.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation.supply_demand import SupplyDemandSimulator
from simulation.weather_impact import WeatherImpactSimulator

class WhatIfMarketSimulator:
    """
    Simulates macro shocks and counterfactual policy/climatic scenarios on agricultural prices.
    """
    def __init__(self):
        self.sd_sim = SupplyDemandSimulator()
        self.weather_sim = WeatherImpactSimulator()

    def simulate_scenario(
        self,
        crop: str,
        base_price: float,
        base_supply_tonnes: float = 120.0,
        base_demand_index: float = 100.0,
        production_change_pct: float = 0.0,
        demand_change_pct: float = 0.0,
        rainfall_anomaly_pct: float = 0.0,
        transport_cost_multiplier: float = 1.0,
        export_restricted: bool = False,
        sudden_glut_arrival_tonnes: float = 0.0
    ) -> Dict[str, Any]:
        """
        Runs comprehensive composite what-if scenario.
        """
        # Weather impact component
        weather_res = self.weather_sim.simulate_weather_shock(
            crop=crop,
            base_price=base_price,
            rainfall_anomaly_pct=rainfall_anomaly_pct
        )

        # Production changes
        # Weather damages reduce production
        net_production_change = production_change_pct - weather_res["yield_damage_pct"]
        new_supply = base_supply_tonnes * (1.0 + (net_production_change / 100.0)) + sudden_glut_arrival_tonnes
        new_supply = max(10.0, new_supply)

        # Demand changes
        # Export ban reduces domestic market clearing demand by 18-25%
        export_demand_penalty = -20.0 if export_restricted else 0.0
        net_demand_change = demand_change_pct + export_demand_penalty
        new_demand = base_demand_index * (1.0 + (net_demand_change / 100.0))
        new_demand = max(20.0, new_demand)

        # Supply-demand equilibrium
        sd_res = self.sd_sim.simulate(
            crop=crop,
            base_price=base_price,
            base_supply_tonnes=base_supply_tonnes,
            new_supply_tonnes=new_supply,
            base_demand_index=base_demand_index,
            new_demand_index=new_demand
        )

        sim_price = sd_res["new_simulated_price"]

        # Transport cost effect (retail price spread vs farm-gate price)
        logistics_markup = 0.0
        if transport_cost_multiplier > 1.0:
            # High freight costs widen the spread: farm-gate drops slightly while consumer terminal price increases
            logistics_markup = base_price * 0.04 * (transport_cost_multiplier - 1.0)

        terminal_consumer_price = round(sim_price + logistics_markup, 0)
        farm_gate_realization = round(max(200.0, sim_price - (logistics_markup * 0.4)), 0)

        # Generate scenario insights
        insights = []
        if rainfall_anomaly_pct < -30.0:
            insights.append("Drought severity is constricting crop arrivals, driving upward price pressure.")
        elif rainfall_anomaly_pct > 30.0:
            insights.append("Excess rainfall is causing harvesting bottlenecks and shelf-life degradation.")
        
        if export_restricted:
            insights.append("Government export restriction creates domestic inventory buildup, putting downward pressure on prices.")

        if production_change_pct > 20.0:
            insights.append(f"Bumper harvest (+{production_change_pct:.0f}%) risks mandi gluts without cold storage absorption.")

        if transport_cost_multiplier > 1.5:
            insights.append("Diesel freight hike is expanding the farm-gate to consumer price spread.")

        return {
            "crop": crop,
            "base_price": base_price,
            "simulated_mandi_price": sim_price,
            "simulated_farm_gate_price": farm_gate_realization,
            "simulated_consumer_price": terminal_consumer_price,
            "price_delta": round(sim_price - base_price, 0),
            "price_delta_pct": round(((sim_price - base_price) / base_price) * 100.0, 2),
            "effective_supply_tonnes": round(new_supply, 1),
            "effective_demand_index": round(new_demand, 1),
            "supply_delta_pct": round(((new_supply - base_supply_tonnes) / base_supply_tonnes) * 100.0, 1),
            "demand_delta_pct": round(((new_demand - base_demand_index) / base_demand_index) * 100.0, 1),
            "export_restricted": export_restricted,
            "transport_multiplier": transport_cost_multiplier,
            "insights": insights,
            "market_state": sd_res["market_state"]
        }

    def run_multi_agent_simulation(
        self,
        crop: str,
        base_price: float,
        num_farmers: int = 50,
        num_traders: int = 8,
        num_wholesalers: int = 4
    ) -> Dict[str, Any]:
        """
        Simulates agricultural multi-agent marketplace:
        Farmers -> Commission Agents / Traders -> Wholesalers -> Retailers -> Consumers.
        """
        import numpy as np
        np.random.seed(42)

        # Farmer agent asks: reservation price distribution around base price
        farmer_asks = np.random.normal(loc=base_price * 0.96, scale=base_price * 0.05, size=num_farmers)
        farmer_supplies = np.random.uniform(15.0, 60.0, size=num_farmers) # quintals each

        # Trader bids
        trader_margins = np.random.uniform(0.05, 0.09, size=num_traders)
        
        # Wholesaler bids (derived from consumer willingness-to-pay)
        consumer_demand_price = base_price * 1.35
        wholesaler_bids = np.random.normal(loc=base_price * 1.08, scale=base_price * 0.04, size=num_wholesalers)

        # Clearing price via double auction mechanism
        clearing_price = float(np.median(farmer_asks) * 0.45 + np.median(wholesaler_bids) * 0.55)
        total_volume_traded = float(np.sum(farmer_supplies[farmer_asks <= clearing_price]))

        # Value chain margin breakdown
        farm_gate_share = clearing_price
        trader_commission = round(clearing_price * 0.04, 1)
        wholesaler_margin = round(clearing_price * 0.12, 1)
        retailer_margin = round(clearing_price * 0.18, 1)
        final_consumer_price = round(farm_gate_share + trader_commission + wholesaler_margin + retailer_margin, 1)

        margin_breakdown = [
            {"stakeholder": "Farmer (Farm-Gate)", "amount": round(farm_gate_share, 0), "share_pct": round((farm_gate_share / final_consumer_price) * 100, 1)},
            {"stakeholder": "Commission Agent / Trader", "amount": round(trader_commission, 0), "share_pct": round((trader_commission / final_consumer_price) * 100, 1)},
            {"stakeholder": "Wholesale Distributor", "amount": round(wholesaler_margin, 0), "share_pct": round((wholesaler_margin / final_consumer_price) * 100, 1)},
            {"stakeholder": "Retailer / Local Vendor", "amount": round(retailer_margin, 0), "share_pct": round((retailer_margin / final_consumer_price) * 100, 1)},
        ]

        return {
            "crop": crop,
            "clearing_mandi_price": round(clearing_price, 0),
            "final_consumer_price": round(final_consumer_price, 0),
            "total_volume_quintals": round(total_volume_traded, 0),
            "num_farmers_transacted": int(np.sum(farmer_asks <= clearing_price)),
            "margin_breakdown": margin_breakdown,
            "farmer_share_of_consumer_rupee": round((farm_gate_share / final_consumer_price) * 100, 1)
        }

