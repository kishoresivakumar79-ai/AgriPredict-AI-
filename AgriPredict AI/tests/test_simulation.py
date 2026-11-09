"""
Unit Tests for Economic, Weather, Storage, and Profit Simulation Engines.
"""
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation.supply_demand import SupplyDemandSimulator
from simulation.weather_impact import WeatherImpactSimulator
from simulation.storage_simulator import StorageSimulator
from simulation.profit_simulator import FarmerProfitSimulator

def test_supply_demand_equilibrium():
    sim = SupplyDemandSimulator()
    # When supply increases by 50% with fixed demand, price must decrease
    res_glut = sim.simulate(
        crop="Tomato",
        base_price=2000.0,
        base_supply_tonnes=100.0,
        new_supply_tonnes=150.0,
        base_demand_index=100.0,
        new_demand_index=100.0
    )
    assert res_glut["new_simulated_price"] < 2000.0
    assert res_glut["price_change_pct"] < 0.0

    # When demand increases by 50% with fixed supply, price must increase
    res_scarcity = sim.simulate(
        crop="Tomato",
        base_price=2000.0,
        base_supply_tonnes=100.0,
        new_supply_tonnes=100.0,
        base_demand_index=100.0,
        new_demand_index=150.0
    )
    assert res_scarcity["new_simulated_price"] > 2000.0
    assert res_scarcity["price_change_pct"] > 0.0

def test_weather_impact_simulation():
    w_sim = WeatherImpactSimulator()
    res = w_sim.simulate_weather_shock(
        crop="Tomato",
        base_price=1500.0,
        rainfall_anomaly_pct=50.0,
        temp_anomaly_c=2.5
    )
    assert res["yield_damage_pct"] > 0.0
    assert res["simulated_price"] > 1500.0
    assert len(res["causal_chain"]) == 5

def test_storage_decision_simulator():
    s_sim = StorageSimulator()
    res = s_sim.simulate_strategies(
        crop="Tomato",
        quantity_quintals=100.0,
        current_price=1500.0,
        price_7d=1700.0,
        price_15d=2000.0,
        price_30d=1850.0,
        use_cold_storage=True
    )
    assert len(res["strategies"]) == 4
    assert res["strategies"][0]["strategy"] == "Immediate Sale"
    assert res["max_net_realization"] > 0

def test_farmer_profit_calculation():
    p_sim = FarmerProfitSimulator()
    p_res = p_sim.calculate_profit(
        crop="Tomato",
        quantity_quintals=100.0,
        selling_price_per_q=2000.0
    )
    assert p_res["gross_revenue"] == 200000.0
    assert p_res["total_expenses"] > 0.0
    assert p_res["break_even_price_per_q"] > 0.0

