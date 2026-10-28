"""
Elexon BMRS API client.

Key findings from live API verification (2026-10-28):
- FUELHH: use /stream endpoint with settlementDateFrom/To — returns all 48 periods per day
  The base /datasets/FUELHH endpoint only returns the ~12 most recent published records.
- WINDFOR: fuelType field is a single "WIND" (combined offshore + onshore)
  Field names: dataset, publishTime, startTime, generation
  Use publishDateTimeFrom / publishDateTimeTo for cutoff-based filtering
- WINDFOR startTime is UTC; GB settlement day starts at 23:00 UTC (period 1 = 23:00-23:30 UTC)
- No API key required; API is publicly accessible
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

ELEXON_BASE = os.getenv(
    "ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1"
).rstrip("/")

# Day-ahead gate closure: 11:00 UTC on the day before delivery
# We use 10:59 UTC as the inclusive upper bound to avoid boundary ambiguity
DA_CUTOFF_HOUR = 10
DA_CUTOFF_MINUTE = 59


def _cutoff_for_delivery_day(delivery_date: date) -> datetime:
    """
    Returns the day-ahead forecast cutoff datetime for a given delivery date.
    Cutoff = 10:59 UTC on (delivery_date - 1), representing the last moment
    before the 11:00 UTC EPEX/N2EX GB day-ahead gate closure.
    """
    prev_day = delivery_date - timedelta(days=1)
    return datetime(
        prev_day.year, prev_day.month, prev_day.day,
        DA_CUTOFF_HOUR, DA_CUTOFF_MINUTE, 0,
        tzinfo=timezone.utc,
    )


def _start_time_to_settlement(start_time: str) -> tuple[date, int]:
    """
    Convert WINDFOR/FUELHH startTime (UTC ISO string) to (settlementDate, period).

    GB electricity settlement day begins at 23:00 UTC (period 1 = 23:00–23:30 UTC
    of the *previous* calendar day). Period 48 = 22:30–23:00 UTC of settlement date.
    """
    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    # Shift forward 1 hour: 23:00 UTC maps to 00:00 of the settlement date
    adjusted = dt + timedelta(hours=1)
    sdate = adjusted.date()
    # Day start = 23:00 UTC of previous calendar day
    day_start_utc = datetime(sdate.year, sdate.month, sdate.day, 0, 0, 0,
                             tzinfo=timezone.utc) - timedelta(hours=1)
    period = int((dt - day_start_utc).total_seconds() / 1800) + 1
    return sdate, period


async def fetch_actuals(
    date_from: date,
    date_to: date,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch actual half-hourly wind generation (FUELHH) for a date range.

    Uses the /stream endpoint which reliably returns all 48 settlement periods
    per day (the base endpoint only returns the most recently published ~12).

    Returns a list of dicts with keys:
        settlementDate (str YYYY-MM-DD), settlementPeriod (int 1-48),
        startTime (str UTC ISO), generation (float MW)
    """
    url = f"{ELEXON_BASE}/datasets/FUELHH/stream"
    params = {
        "settlementDateFrom": date_from.isoformat(),
        "settlementDateTo": date_to.isoformat(),
    }

    async def _do_fetch(c: httpx.AsyncClient) -> list[dict[str, Any]]:
        resp = await c.get(url, params=params, timeout=60.0)
        resp.raise_for_status()
        raw = resp.json()
        items = raw.get("data", raw) if isinstance(raw, dict) else raw
        wind = [r for r in items if r.get("fuelType") == "WIND"]
        return [
            {
                "settlementDate": r["settlementDate"],
                "settlementPeriod": r["settlementPeriod"],
                "startTime": r["startTime"],
                "generation_mw": r["generation"],
            }
            for r in wind
        ]

    if client:
        return await _do_fetch(client)
    async with httpx.AsyncClient() as c:
        return await _do_fetch(c)


async def fetch_forecasts_day_ahead(
    delivery_date_from: date,
    delivery_date_to: date,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch day-ahead WINDFOR forecasts for each delivery date in range.

    For each delivery day D, selects the WINDFOR run with the latest publishTime
    that is <= 10:59 UTC on (D-1) — i.e., the last forecast available before
    the day-ahead market gate closes at 11:00 UTC.

    This strictly avoids any future-data leakage: only information that was
    available to a day-ahead market participant is used.

    Returns a list of dicts with keys:
        settlementDate (str YYYY-MM-DD), settlementPeriod (int 1-48),
        startTime (str UTC ISO), forecast_mw (float), publishTime (str UTC ISO),
        forecastRunLabel (str, e.g. "DA 05:30Z")
    """
    # Fetch all WINDFOR published in the window covering our delivery dates
    # We go from (date_from - 2 days) to (date_to - 1 day) 11:00 UTC to capture
    # all possible day-ahead runs for the full date range
    pub_from = datetime(
        (delivery_date_from - timedelta(days=2)).year,
        (delivery_date_from - timedelta(days=2)).month,
        (delivery_date_from - timedelta(days=2)).day,
        0, 0, 0, tzinfo=timezone.utc,
    )
    pub_to = datetime(
        (delivery_date_to - timedelta(days=1)).year,
        (delivery_date_to - timedelta(days=1)).month,
        (delivery_date_to - timedelta(days=1)).day,
        DA_CUTOFF_HOUR, DA_CUTOFF_MINUTE, 0, tzinfo=timezone.utc,
    )

    url = f"{ELEXON_BASE}/datasets/WINDFOR/stream"
    params = {
        "publishDateTimeFrom": pub_from.isoformat().replace("+00:00", "Z"),
        "publishDateTimeTo": pub_to.isoformat().replace("+00:00", "Z"),
    }

    async def _do_fetch(c: httpx.AsyncClient) -> list[dict[str, Any]]:
        resp = await c.get(url, params=params, timeout=120.0)
        resp.raise_for_status()
        raw = resp.json()
        items = raw.get("data", raw) if isinstance(raw, dict) else raw

        # Group records by delivery (settlementDate, settlementPeriod), keeping
        # the run with the latest publishTime <= cutoff for that delivery date
        # Key: (settlementDate_str, period_int) → best record so far
        best: dict[tuple[str, int], dict[str, Any]] = {}

        for r in items:
            start_time = r.get("startTime", "")
            pub_time_str = r.get("publishTime", "")
            if not start_time or not pub_time_str:
                continue

            sdate, period = _start_time_to_settlement(start_time)

            # Only keep records for delivery dates in our requested range
            if not (delivery_date_from <= sdate <= delivery_date_to):
                continue

            pub_dt = datetime.fromisoformat(pub_time_str.replace("Z", "+00:00"))
            cutoff = _cutoff_for_delivery_day(sdate)

            # Strict cutoff: only use runs published before gate close
            if pub_dt > cutoff:
                continue

            # WINDFOR forecasts are published at hourly resolution (24 points per day).
            # Each hourly forecast MW represents the expected average power rate over
            # that 1-hour block, spanning two 30-minute settlement periods (p and p+1).
            periods_to_map = [period, period + 1] if (period % 2 == 1 and period < 48) else [period]

            for p in periods_to_map:
                key = (str(sdate), p)
                existing = best.get(key)
                if existing is None or pub_dt > existing["_pub_dt"]:
                    best[key] = {**r, "_pub_dt": pub_dt, "_sdate": sdate, "_period": p}

        results = []
        for (sdate_str, period), r in sorted(best.items()):
            pub_dt = r["_pub_dt"]
            results.append({
                "settlementDate": sdate_str,
                "settlementPeriod": period,
                "startTime": r["startTime"],
                "forecast_mw": r["generation"],
                "publishTime": r["publishTime"],
                "forecastRunLabel": f"DA {pub_dt.strftime('%H:%MZ')}",
            })
        return results

    if client:
        return await _do_fetch(client)
    async with httpx.AsyncClient() as c:
        return await _do_fetch(c)

