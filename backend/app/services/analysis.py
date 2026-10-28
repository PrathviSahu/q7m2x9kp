"""
Forecast accuracy analysis module.

Computes MAE, RMSE, signed Bias, and MAPE by joining actual (FUELHH)
and day-ahead forecast (WINDFOR) records on (settlementDate, settlementPeriod).
Handles missing / unmatched intervals cleanly.
"""
from __future__ import annotations

import math
from typing import Any


# Minimum actual generation (MW) for MAPE calculation.
# Periods with very low actual output inflate % error; we exclude them.
MAPE_MIN_ACTUAL_MW = 50.0


def _safe_float(val: Any) -> float | None:
    """Convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def join_actuals_and_forecasts(
    actuals: list[dict[str, Any]],
    forecasts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Inner-join actuals and forecasts on (settlementDate, settlementPeriod).

    Returns a list of joined records with keys:
        settlementDate, settlementPeriod, startTime,
        actual_mw, forecast_mw, publishTime, forecastRunLabel,
        error_mw (forecast - actual), has_actual, has_forecast
    """
    # Build lookup: (date, period) → actual record
    actual_map: dict[tuple[str, int], dict[str, Any]] = {}
    for r in actuals:
        key = (r["settlementDate"], int(r["settlementPeriod"]))
        actual_map[key] = r

    # Build lookup: (date, period) → forecast record
    forecast_map: dict[tuple[str, int], dict[str, Any]] = {}
    for r in forecasts:
        key = (r["settlementDate"], int(r["settlementPeriod"]))
        forecast_map[key] = r

    all_keys = sorted(set(actual_map.keys()) | set(forecast_map.keys()))
    joined = []
    for key in all_keys:
        sdate, period = key
        act = actual_map.get(key)
        fcast = forecast_map.get(key)

        actual_mw = _safe_float(act["generation_mw"]) if act else None
        forecast_mw = _safe_float(fcast["forecast_mw"]) if fcast else None
        error_mw = (
            forecast_mw - actual_mw
            if actual_mw is not None and forecast_mw is not None
            else None
        )

        joined.append({
            "settlementDate": sdate,
            "settlementPeriod": period,
            "startTime": (act or fcast or {}).get("startTime", ""),
            "actual_mw": actual_mw,
            "forecast_mw": forecast_mw,
            "publishTime": fcast["publishTime"] if fcast else None,
            "forecastRunLabel": fcast["forecastRunLabel"] if fcast else None,
            "error_mw": error_mw,
            "has_actual": act is not None,
            "has_forecast": fcast is not None,
        })
    return joined


def compute_metrics(
    joined: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compute overall and per-day accuracy metrics from joined records.

    Returns:
        overall: dict with mae, rmse, bias, mape, matched_periods, total_periods, coverage
        by_date: dict[str, dict] with same keys per settlement date
    """
    # Only use matched pairs (both actual and forecast present)
    matched = [r for r in joined if r["error_mw"] is not None]
    total = len(joined)
    n = len(matched)

    def _metrics_for(records: list[dict[str, Any]]) -> dict[str, Any]:
        errors = [r["error_mw"] for r in records if r["error_mw"] is not None]
        if not errors:
            return {
                "mae_mw": None, "rmse_mw": None, "bias_mw": None,
                "mape_pct": None, "matched_periods": 0, "coverage": 0.0,
            }

        n_local = len(errors)
        mae = sum(abs(e) for e in errors) / n_local
        rmse = math.sqrt(sum(e ** 2 for e in errors) / n_local)
        bias = sum(errors) / n_local

        # MAPE: only where actual >= threshold
        mape_pairs = [
            (r["error_mw"], r["actual_mw"])
            for r in records
            if r["error_mw"] is not None and r["actual_mw"] is not None
            and r["actual_mw"] >= MAPE_MIN_ACTUAL_MW
        ]
        mape = (
            sum(abs(e) / a * 100 for e, a in mape_pairs) / len(mape_pairs)
            if mape_pairs else None
        )

        # Coverage = matched / 48 per day (or total possible)
        total_local = len(records)
        coverage = n_local / total_local if total_local else 0.0

        return {
            "mae_mw": round(mae, 2),
            "rmse_mw": round(rmse, 2),
            "bias_mw": round(bias, 2),
            "mape_pct": round(mape, 2) if mape is not None else None,
            "matched_periods": n_local,
            "coverage": round(coverage, 4),
        }

    # Overall metrics
    overall = _metrics_for(matched)
    overall["total_periods"] = total
    overall["matched_periods"] = n

    # Per-day metrics
    from collections import defaultdict
    by_date_raw: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in joined:
        by_date_raw[r["settlementDate"]].append(r)

    by_date: dict[str, dict[str, Any]] = {}
    for d, records in sorted(by_date_raw.items()):
        matched_day = [r for r in records if r["error_mw"] is not None]
        by_date[d] = _metrics_for(matched_day)
        by_date[d]["total_periods"] = len(records)

    return {"overall": overall, "by_date": by_date}

