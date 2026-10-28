"""
Tests for the Elexon client — cutoff logic and settlement period mapping.
These are pure unit tests; no HTTP calls are made.
"""
import pytest
from datetime import date, datetime, timezone
from app.services.elexon import _cutoff_for_delivery_day, _start_time_to_settlement


class TestCutoffLogic:
    def test_cutoff_is_day_before(self):
        delivery = date(2026, 1, 15)
        cutoff = _cutoff_for_delivery_day(delivery)
        assert cutoff.date() == date(2026, 1, 14)

    def test_cutoff_time_is_1059_utc(self):
        delivery = date(2026, 1, 15)
        cutoff = _cutoff_for_delivery_day(delivery)
        assert cutoff.hour == 10
        assert cutoff.minute == 59
        assert cutoff.tzinfo == timezone.utc

    def test_cutoff_excludes_1100_run(self):
        """A forecast published at 11:00 UTC on D-1 must NOT be used."""
        delivery = date(2026, 1, 15)
        cutoff = _cutoff_for_delivery_day(delivery)
        run_at_1100 = datetime(2026, 1, 14, 11, 0, 0, tzinfo=timezone.utc)
        assert run_at_1100 > cutoff  # correctly excluded

    def test_cutoff_includes_0930_run(self):
        """A forecast published at 09:30 UTC on D-1 must be included."""
        delivery = date(2026, 1, 15)
        cutoff = _cutoff_for_delivery_day(delivery)
        run_at_0930 = datetime(2026, 1, 14, 9, 30, 0, tzinfo=timezone.utc)
        assert run_at_0930 <= cutoff  # correctly included

    def test_month_boundary(self):
        delivery = date(2026, 2, 1)
        cutoff = _cutoff_for_delivery_day(delivery)
        assert cutoff.date() == date(2026, 1, 31)


class TestSettlementMapping:
    def test_period_1_is_0000_utc_same_day(self):
        """Period 1 = 00:00 to 00:30 UTC on the settlement date (GMT in January)."""
        sdate, period = _start_time_to_settlement("2026-01-15T00:00:00Z")
        assert str(sdate) == "2026-01-15"
        assert period == 1

    def test_period_2_is_0030_utc(self):
        sdate, period = _start_time_to_settlement("2026-01-15T00:30:00Z")
        assert str(sdate) == "2026-01-15"
        assert period == 2

    def test_period_48_is_2330_utc_same_day(self):
        """Period 48 = 23:30 to 24:00 UTC on the settlement date itself."""
        sdate, period = _start_time_to_settlement("2026-01-15T23:30:00Z")
        assert str(sdate) == "2026-01-15"
        assert period == 48

    def test_midday_period(self):
        """12:00 UTC = period 25 (12:00-12:30 UTC)."""
        sdate, period = _start_time_to_settlement("2026-01-15T12:00:00Z")
        assert str(sdate) == "2026-01-15"
        assert period == 25

    def test_new_year_first_period(self):
        """Period 1 of Jan 1 starts at 00:00 UTC Jan 1."""
        sdate, period = _start_time_to_settlement("2026-01-01T00:00:00Z")
        assert str(sdate) == "2026-01-01"
        assert period == 1

