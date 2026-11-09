"""
FastAPI Routes for Supply-Demand, Profit, Storage, and What-If Simulations.
"""
from fastapi import APIRouter, Body
from typing import Dict, Any, Optional

from simulation.supply_demand import SupplyDemandSimulator
from simulation.storage_simulator import StorageSimulator
from simulation.profit_simulator import FarmerProfitSimulator
from simulation.market_simulator import WhatIfMarketSimulator
from backend.services.assistant_service import FarmerAssistant
from backend.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/simulation", tags=["Economic Simulation"])

sd_sim = SupplyDemandSimulator()
storage_sim = StorageSimulator()
profit_sim = FarmerProfitSimulator()
whatif_sim = WhatIfMarketSimulator()
assistant = FarmerAssistant()
rec_service = RecommendationService()

@router.get("/supply-demand")
def simulate_supply_demand(
    crop: str = "Tomato",
    base_price: float = 1800.0,
    base_supply: float = 120.0,
    new_supply: float = 140.0,
    base_demand: float = 100.0,
    new_demand: float = 100.0
):
    """Simulates market price equilibrium shift under supply/demand changes."""
    return sd_sim.simulate(
        crop=crop,
        base_price=base_price,
        base_supply_tonnes=base_supply,
        new_supply_tonnes=new_supply,
        base_demand_index=base_demand,
        new_demand_index=new_demand
    )

@router.get("/storage")
def simulate_storage_decision(
    crop: str = "Tomato",
    quantity_quintals: float = 100.0,
    current_price: float = 1800.0,
    price_7d: float = 1950.0,
    price_15d: float = 2200.0,
    price_30d: float = 2100.0,
    use_cold_storage: bool = True
):
    """Compares immediate sale vs 7, 15, and 30 day holding strategies."""
    return storage_sim.simulate_strategies(
        crop=crop,
        quantity_quintals=quantity_quintals,
        current_price=current_price,
        price_7d=price_7d,
        price_15d=price_15d,
        price_30d=price_30d,
        use_cold_storage=use_cold_storage
    )

@router.get("/profit")
def calculate_farmer_profit(
    crop: str = "Tomato",
    quantity_quintals: float = 100.0,
    selling_price: float = 1800.0,
    transport_cost: float = 5000.0,
    storage_cost: float = 0.0
):
    """Calculates farmer production costs, revenue, break-even, and net profit."""
    return profit_sim.calculate_profit(
        crop=crop,
        quantity_quintals=quantity_quintals,
        selling_price_per_q=selling_price,
        transport_cost_total=transport_cost,
        storage_cost_total=storage_cost
    )

@router.get("/what-if")
def simulate_what_if_scenario(
    crop: str = "Tomato",
    base_price: float = 1800.0,
    production_change_pct: float = 0.0,
    demand_change_pct: float = 0.0,
    rainfall_anomaly_pct: float = 0.0,
    transport_cost_multiplier: float = 1.0,
    export_restricted: bool = False,
    sudden_glut_arrival_tonnes: float = 0.0
):
    """Simulates multi-parameter macro shocks and policy scenarios."""
    return whatif_sim.simulate_scenario(
        crop=crop,
        base_price=base_price,
        production_change_pct=production_change_pct,
        demand_change_pct=demand_change_pct,
        rainfall_anomaly_pct=rainfall_anomaly_pct,
        transport_cost_multiplier=transport_cost_multiplier,
        export_restricted=export_restricted,
        sudden_glut_arrival_tonnes=sudden_glut_arrival_tonnes
    )

@router.get("/digital-twin")
def run_agricultural_digital_twin(
    crop: str = "Tomato",
    base_price: float = 1800.0,
    num_farmers: int = 50
):
    """Simulates agricultural market participants: Farmers, Traders, Wholesalers, Retailers."""
    return whatif_sim.run_multi_agent_simulation(
        crop=crop,
        base_price=base_price,
        num_farmers=num_farmers
    )

@router.post("/assistant/ask")
def ask_farmer_assistant(payload: Dict[str, str] = Body(...)):
    """Conversational AI Agricultural Advisor."""
    question = payload.get("question", "")
    return assistant.answer_query(question)

@router.get("/advisory/full")
def get_farmer_advisory(
    crop: str = "Tomato",
    market: str = "Salem",
    quantity_quintals: float = 100.0,
    horizon_days: int = 15
):
    """Comprehensive farmer decision support advisory."""
    return rec_service.get_full_farmer_advisory(
        crop=crop,
        current_market=market,
        quantity_quintals=quantity_quintals,
        horizon_days=horizon_days
    )
