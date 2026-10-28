"""
Tests for the analysis module — accuracy metric calculations.
These are pure unit tests with no external dependencies.
"""
import math
import pytest
from app.services.analysis import (
    join_actuals_and_forecasts,
    compute_metrics,
    MAPE_MIN_ACTUAL_MW,
)


def make_actual(date="2026-01-01", period=1, mw=1000.0):
    return {
        "settlementDate": date,
        "settlementPeriod": period,
        "startTime": f"{date}T00:00:00Z",
        "generation_mw": mw,
    }


def make_forecast(date="2026-01-01", period=1, mw=1100.0, pub="2026-01-01T05:30:00Z"):
    return {
        "settlementDate": date,
        "settlementPeriod": period,
        "startTime": f"{date}T00:00:00Z",
        "forecast_mw": mw,
        "publishTime": pub,
        "forecastRunLabel": "DA 05:30Z",
    }


class TestJoinActualsAndForecasts:
    def test_perfect_match(self):
        actuals = [make_actual("2026-01-01", 1, 1000)]
        forecasts = [make_forecast("2026-01-01", 1, 1050)]
        result = join_actuals_and_forecasts(actuals, forecasts)
        assert len(result) == 1
        assert result[0]["actual_mw"] == 1000
        assert result[0]["forecast_mw"] == 1050
        assert result[0]["error_mw"] == pytest.approx(50.0)
        assert result[0]["has_actual"] is True
        assert result[0]["has_forecast"] is True

    def test_missing_forecast(self):
        actuals = [make_actual("2026-01-01", 1, 1000)]
        result = join_actuals_and_forecasts(actuals, [])
        assert len(result) == 1
        assert result[0]["actual_mw"] == 1000
        assert result[0]["forecast_mw"] is None
        assert result[0]["error_mw"] is None
        assert result[0]["has_actual"] is True
        assert result[0]["has_forecast"] is False

    def test_missing_actual(self):
        forecasts = [make_forecast("2026-01-01", 1, 1050)]
        result = join_actuals_and_forecasts([], forecasts)
        assert len(result) == 1
        assert result[0]["actual_mw"] is None
        assert result[0]["forecast_mw"] == 1050
        assert result[0]["error_mw"] is None

    def test_multiple_periods_sorted(self):
        actuals = [make_actual("2026-01-01", p, float(p * 100)) for p in range(1, 5)]
        forecasts = [make_forecast("2026-01-01", p, float(p * 110)) for p in range(1, 5)]
        result = join_actuals_and_forecasts(actuals, forecasts)
        assert len(result) == 4
        periods = [r["settlementPeriod"] for r in result]
        assert periods == [1, 2, 3, 4]

    def test_over_and_under_forecast_errors(self):
        actuals = [make_actual("2026-01-01", 1, 1000)]
        forecasts = [make_forecast("2026-01-01", 1, 800)]  # under-forecast
        result = join_actuals_and_forecasts(actuals, forecasts)
        assert result[0]["error_mw"] == pytest.approx(-200.0)


class TestComputeMetrics:
    def _make_joined(self, pairs: list[tuple[float, float]], date="2026-01-01"):
        """Helper: list of (actual_mw, forecast_mw) → joined records."""
        records = []
        for i, (a, f) in enumerate(pairs):
            records.append({
                "settlementDate": date,
                "settlementPeriod": i + 1,
                "startTime": f"{date}T00:00:00Z",
                "actual_mw": a,
                "forecast_mw": f,
                "publishTime": f"{date}T05:30:00Z",
                "forecastRunLabel": "DA 05:30Z",
                "error_mw": f - a,
                "has_actual": True,
                "has_forecast": True,
            })
        return records

    def test_mae_exact(self):
        # errors: +100, -100 → MAE = 100
        joined = self._make_joined([(1000, 1100), (1000, 900)])
        metrics = compute_metrics(joined)
        assert metrics["overall"]["mae_mw"] == pytest.approx(100.0)

    def test_rmse_exact(self):
        # errors: +100, -100 → RMSE = 100
        joined = self._make_joined([(1000, 1100), (1000, 900)])
        metrics = compute_metrics(joined)
        assert metrics["overall"]["rmse_mw"] == pytest.approx(100.0)

    def test_bias_positive(self):
        # systematic over-forecast
        joined = self._make_joined([(1000, 1200), (1000, 1200)])
        metrics = compute_metrics(joined)
        assert metrics["overall"]["bias_mw"] == pytest.approx(200.0)

    def test_bias_zero(self):
        joined = self._make_joined([(1000, 1100), (1000, 900)])
        metrics = compute_metrics(joined)
        assert metrics["overall"]["bias_mw"] == pytest.approx(0.0)

    def test_mape_excludes_low_actual(self):
        # actual = 10 MW (below threshold) → excluded from MAPE
        joined = self._make_joined([(10, 100), (1000, 1100)])
        metrics = compute_metrics(joined)
        # Only second record used: |100| / 1000 * 100 = 10%
        assert metrics["overall"]["mape_pct"] == pytest.approx(10.0)

    def test_mape_none_when_all_below_threshold(self):
        joined = self._make_joined([(1, 100), (5, 200)])
        metrics = compute_metrics(joined)
        assert metrics["overall"]["mape_pct"] is None

    def test_coverage(self):
        # 2 matched, 1 unmatched
        joined = self._make_joined([(1000, 1100), (1000, 900)])
        # Add an unmatched record
        joined.append({
            "settlementDate": "2026-01-01",
            "settlementPeriod": 3,
            "startTime": "",
            "actual_mw": None,
            "forecast_mw": 1000,
            "publishTime": None,
            "forecastRunLabel": None,
            "error_mw": None,
            "has_actual": False,
            "has_forecast": True,
        })
        metrics = compute_metrics(joined)
        assert metrics["overall"]["matched_periods"] == 2
        assert metrics["overall"]["total_periods"] == 3

    def test_by_date_breakdown(self):
        j1 = self._make_joined([(1000, 1100)], date="2026-01-01")
        j2 = self._make_joined([(2000, 1800)], date="2026-01-02")
        metrics = compute_metrics(j1 + j2)
        assert "2026-01-01" in metrics["by_date"]
        assert "2026-01-02" in metrics["by_date"]
        assert metrics["by_date"]["2026-01-01"]["mae_mw"] == pytest.approx(100.0)
        assert metrics["by_date"]["2026-01-02"]["mae_mw"] == pytest.approx(200.0)

    def test_empty_joined(self):
        metrics = compute_metrics([])
        assert metrics["overall"]["mae_mw"] is None
        assert metrics["overall"]["matched_periods"] == 0


class TestEdgeCases:
    def test_zero_actual_excluded_from_mape(self):
        joined = [{
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "startTime": "",
            "actual_mw": 0.0,
            "forecast_mw": 500.0,
            "publishTime": None,
            "forecastRunLabel": None,
            "error_mw": 500.0,
            "has_actual": True,
            "has_forecast": True,
        }]
        metrics = compute_metrics(joined)
        # 0 MW < MAPE_MIN_ACTUAL_MW → MAPE should be None
        assert metrics["overall"]["mape_pct"] is None

    def test_single_perfect_forecast(self):
        joined = [{
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "startTime": "",
            "actual_mw": 1000.0,
            "forecast_mw": 1000.0,
            "publishTime": None,
            "forecastRunLabel": None,
            "error_mw": 0.0,
            "has_actual": True,
            "has_forecast": True,
        }]
        metrics = compute_metrics(joined)
        assert metrics["overall"]["mae_mw"] == 0.0
        assert metrics["overall"]["rmse_mw"] == 0.0
        assert metrics["overall"]["bias_mw"] == 0.0
        assert metrics["overall"]["mape_pct"] == 0.0

