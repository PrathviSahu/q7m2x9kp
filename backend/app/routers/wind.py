"""
Wind data API router.

Endpoints:
  GET /api/wind/actuals   — actual half-hourly wind generation (FUELHH)
  GET /api/wind/forecasts — day-ahead wind forecasts (WINDFOR)
  GET /api/wind/accuracy  — joined series + accuracy metrics
"""
from __future__ import annotations

import time
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.elexon import fetch_actuals, fetch_forecasts_day_ahead
from app.services.analysis import join_actuals_and_forecasts, compute_metrics
from app.models import ActualRecord, ForecastRecord, AccuracyResponse

router = APIRouter()

# Default to January 2026 — the assessment period
DEFAULT_FROM = date(2026, 1, 1)
DEFAULT_TO = date(2026, 1, 31)
MAX_RANGE_DAYS = 62

# Simple in-memory cache: (date_from, date_to) -> (timestamp, data)
_accuracy_cache: dict[tuple[date, date], tuple[float, dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache for historical dataset


def _validate_dates(date_from: date, date_to: date) -> None:
    if date_from > date_to:
        raise HTTPException(400, "date_from must be <= date_to")
    if (date_to - date_from).days > MAX_RANGE_DAYS:
        raise HTTPException(400, f"Date range cannot exceed {MAX_RANGE_DAYS} days")


@router.get("/actuals", response_model=list[ActualRecord])
async def get_actuals(
    date_from: date = Query(default=DEFAULT_FROM, description="Start date (YYYY-MM-DD)"),
    date_to: date = Query(default=DEFAULT_TO, description="End date (YYYY-MM-DD)"),
) -> list[dict]:
    """
    Half-hourly actual wind generation (MW) from FUELHH.
    Returns all 48 settlement periods per day in the requested range.
    """
    _validate_dates(date_from, date_to)
    try:
        return await fetch_actuals(date_from, date_to)
    except Exception as exc:
        raise HTTPException(502, f"Elexon FUELHH fetch failed: {exc}") from exc


@router.get("/forecasts", response_model=list[ForecastRecord])
async def get_forecasts(
    date_from: date = Query(default=DEFAULT_FROM, description="Delivery start date (YYYY-MM-DD)"),
    date_to: date = Query(default=DEFAULT_TO, description="Delivery end date (YYYY-MM-DD)"),
) -> list[dict]:
    """
    Day-ahead wind generation forecasts (MW) from WINDFOR.

    For each delivery half-hour, returns the forecast from the last WINDFOR run
    published before 11:00 UTC on the preceding day (day-ahead gate cutoff).
    No future-data leakage.
    """
    _validate_dates(date_from, date_to)
    try:
        return await fetch_forecasts_day_ahead(date_from, date_to)
    except Exception as exc:
        raise HTTPException(502, f"Elexon WINDFOR fetch failed: {exc}") from exc


@router.get("/accuracy", response_model=AccuracyResponse)
async def get_accuracy(
    date_from: date = Query(default=DEFAULT_FROM, description="Start date (YYYY-MM-DD)"),
    date_to: date = Query(default=DEFAULT_TO, description="End date (YYYY-MM-DD)"),
    refresh: bool = Query(default=False, description="Bypass cache and force fresh fetch"),
) -> dict:
    """
    Joined actual vs day-ahead forecast series + accuracy metrics.

    Returns:
    - overall: MAE, RMSE, Bias, MAPE across the full period
    - by_date: same metrics broken down per settlement day
    - series: full period-level joined timeseries for charting
    """
    _validate_dates(date_from, date_to)
    cache_key = (date_from, date_to)
    now = time.time()

    if not refresh and cache_key in _accuracy_cache:
        cached_time, cached_data = _accuracy_cache[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_data

    try:
        actuals, forecasts = await _fetch_both(date_from, date_to)
    except Exception as exc:
        raise HTTPException(502, f"Elexon data fetch failed: {exc}") from exc

    joined = join_actuals_and_forecasts(actuals, forecasts)
    metrics = compute_metrics(joined)

    result = {
        "overall": metrics["overall"],
        "by_date": metrics["by_date"],
        "series": joined,
    }
    _accuracy_cache[cache_key] = (now, result)
    return result


async def _fetch_both(date_from: date, date_to: date):
    """Fetch actuals and forecasts concurrently."""
    import asyncio
    import httpx

    async with httpx.AsyncClient() as client:
        actuals_task = fetch_actuals(date_from, date_to, client=client)
        forecasts_task = fetch_forecasts_day_ahead(date_from, date_to, client=client)
        actuals, forecasts = await asyncio.gather(actuals_task, forecasts_task)
    return actuals, forecasts

