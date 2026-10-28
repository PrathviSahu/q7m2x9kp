"""
Integration tests for the FastAPI wind endpoints.
Uses TestClient to test /health, /api/wind/actuals, /api/wind/forecasts, /api/wind/accuracy.
"""
from datetime import date
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_date_validation_reversed():
    res = client.get("/api/wind/accuracy?date_from=2026-01-10&date_to=2026-01-05")
    assert res.status_code == 400
    assert "date_from must be <= date_to" in res.json()["detail"]


def test_date_validation_range_too_long():
    res = client.get("/api/wind/accuracy?date_from=2026-01-01&date_to=2026-04-01")
    assert res.status_code == 400
    assert "Date range cannot exceed" in res.json()["detail"]


@patch("app.routers.wind._fetch_both", new_callable=AsyncMock)
def test_accuracy_endpoint(mock_fetch):
    mock_actuals = [
        {"settlementDate": "2026-01-01", "settlementPeriod": 1, "startTime": "2025-12-31T23:00:00Z", "generation_mw": 1000.0},
        {"settlementDate": "2026-01-01", "settlementPeriod": 2, "startTime": "2025-12-31T23:30:00Z", "generation_mw": 1100.0},
    ]
    mock_forecasts = [
        {"settlementDate": "2026-01-01", "settlementPeriod": 1, "startTime": "2025-12-31T23:00:00Z", "forecast_mw": 1050.0, "publishTime": "2025-12-31T09:30:00Z", "forecastRunLabel": "DA 09:30Z"},
        {"settlementDate": "2026-01-01", "settlementPeriod": 2, "startTime": "2025-12-31T23:30:00Z", "forecast_mw": 1050.0, "publishTime": "2025-12-31T09:30:00Z", "forecastRunLabel": "DA 09:30Z"},
    ]
    mock_fetch.return_value = (mock_actuals, mock_forecasts)

    res = client.get("/api/wind/accuracy?date_from=2026-01-01&date_to=2026-01-01&refresh=true")
    assert res.status_code == 200
    data = res.json()
    assert "overall" in data
    assert "by_date" in data
    assert "series" in data
    assert data["overall"]["matched_periods"] == 2
    assert data["overall"]["mae_mw"] == pytest.approx(50.0)
    assert len(data["series"]) == 2
