"""
SQLAlchemy Database Models for Agricultural Market Records, Predictions, and User Scenarios.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from backend.database.db import Base

class CropPriceRecord(Base):
    """Historical and daily recorded mandi price."""
    __tablename__ = "crop_price_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(20), index=True)
    crop = Column(String(50), index=True)
    market = Column(String(50), index=True)
    state = Column(String(50))
    district = Column(String(50))
    modal_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    arrivals_tonnes = Column(Float)
    demand_index = Column(Float)
    temp_avg_c = Column(Float)
    rainfall_mm = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class PredictionAuditLog(Base):
    """Audit log of generated AI predictions."""
    __tablename__ = "prediction_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(50), index=True)
    market = Column(String(50), index=True)
    horizon_days = Column(Integer)
    model_name = Column(String(50))
    current_price = Column(Float)
    predicted_price = Column(Float)
    optimistic_price = Column(Float)
    pessimistic_price = Column(Float)
    recommendation = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class UserScenarioHistory(Base):
    """Logged what-if simulation scenarios."""
    __tablename__ = "user_scenario_history"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(50))
    production_change_pct = Column(Float)
    demand_change_pct = Column(Float)
    rainfall_anomaly_pct = Column(Float)
    base_price = Column(Float)
    simulated_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

