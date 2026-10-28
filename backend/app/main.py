"""
Wind Forecast Dashboard — FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers import wind

app = FastAPI(
    title="Wind Forecast Dashboard API",
    description="UK wind generation forecast vs actual accuracy analysis — January 2026",
    version="1.0.0",
)

# CORS — allow the React frontend origin
_cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
)
allowed_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(wind.router, prefix="/api/wind", tags=["wind"])


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "service": "wind-forecast-dashboard", "version": "1.0.0"}
