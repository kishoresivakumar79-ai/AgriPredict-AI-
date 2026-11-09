"""
FastAPI Main Application Entry Point.
AI-Based Agricultural Market and Price Prediction Simulator Backend.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.db import init_db
from backend.routes import prediction, market, weather, simulation

app = FastAPI(
    title="AgriPredict AI - Agricultural Market Intelligence API",
    description="AI-Driven Crop Price Forecasting, Supply-Demand Equilibrium, and Economic Decision Simulator",
    version="2.5.0"
)

# Enable CORS for local dashboards and cross-origin tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema
init_db()

# Mount API Routers
app.include_router(prediction.router)
app.include_router(market.router)
app.include_router(weather.router)
app.include_router(simulation.router)

@app.get("/")
def root():
    return {
        "app": "AgriPredict AI Backend Service",
        "status": "Online",
        "version": "2.5.0",
        "docs_url": "/docs",
        "description": "AI-Based Agricultural Market and Price Prediction Simulator"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "agripredict-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

