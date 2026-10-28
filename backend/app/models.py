"""
Pydantic response schemas for the Wind Forecast Dashboard API.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class ActualRecord(BaseModel):
    settlementDate: str
    settlementPeriod: int
    startTime: str
    generation_mw: float


class ForecastRecord(BaseModel):
    settlementDate: str
    settlementPeriod: int
    startTime: str
    forecast_mw: float
    publishTime: str
    forecastRunLabel: str


class JoinedRecord(BaseModel):
    settlementDate: str
    settlementPeriod: int
    startTime: str
    actual_mw: Optional[float]
    forecast_mw: Optional[float]
    publishTime: Optional[str]
    forecastRunLabel: Optional[str]
    error_mw: Optional[float]
    has_actual: bool
    has_forecast: bool


class DayMetrics(BaseModel):
    mae_mw: Optional[float]
    rmse_mw: Optional[float]
    bias_mw: Optional[float]
    mape_pct: Optional[float]
    matched_periods: int
    total_periods: int
    coverage: float


class OverallMetrics(DayMetrics):
    pass


class AccuracyResponse(BaseModel):
    overall: OverallMetrics
    by_date: dict[str, DayMetrics]
    series: list[JoinedRecord]

