# UK Wind Forecast Dashboard — Demo Video Walkthrough Outline

This document provides a structured, concise 3–5 minute script/outline for the assessment demo video recording.

---

## Part 1: Architecture, Methodology & Code Walkthrough (~1.5 to 2 minutes)

1. **Introduction & Objective (20s)**:
   - "This is the UK Wind Generation Forecast and Accuracy Analysis Dashboard for January 2026."
   - "Built with a Python FastAPI backend and React Vite frontend, communicating with the official Elexon Insights Solution (BMRS) APIs."

2. **Market Cutoff Logic & Zero Future-Leakage (40s)**:
   - Open `backend/app/services/elexon.py`.
   - Highlight `_cutoff_for_delivery_day` and `fetch_forecasts_day_ahead`:
     - "In GB electricity trading, day-ahead gate closure is 11:00 UTC on day $D-1$."
     - "We filter `WINDFOR` with `publishDateTime <= 10:59 UTC on D-1` to strictly ensure zero future-data leakage."
     - "This ensures we capture only the information available when actual procurement commitments were made."

3. **Resolution Mapping & Accuracy Metrics Engine (30s)**:
   - Open `backend/app/services/analysis.py`.
   - "Settlement periods are 30 minutes (48 per day). `FUELHH` gives all 1,488 actual wind outturn periods for January 2026."
   - "`WINDFOR` provides hourly forecasts which map across adjacent half-hours."
   - "We compute MAE, RMSE, signed Bias, and MAPE (excluding periods below 50 MW to avoid division distortion)."

4. **Automated Testing Suite (20s)**:
   - Terminal demonstration:
     ```bash
     cd backend && .venv/bin/pytest tests/ -v
     cd ../frontend && npm test
     ```
   - Show 30/30 backend tests passing and 8/8 frontend tests passing.

---

## Part 2: Live Application & Dashboard Walkthrough (~1.5 to 2 minutes)

1. **Top-Level KPI Summary Cards**:
   - Show overall MAE, RMSE, signed Bias, MAPE, and coverage (100% matched periods).
   - Explain what the bias indicator signifies (positive = over-forecast, negative = under-forecast).

2. **Time Series Chart (Actuals vs Forecast)**:
   - Switch between high-wind generation days (e.g. winter storms exceeding 15–20 GW) and low-wind periods.
   - Point out how the dashed forecast line tracks actual outturn across the 31 days.

3. **Forecast Error Heatmap Matrix**:
   - Show the 31 × 48 grid (days on the y-axis, settlement periods 1–48 on the x-axis).
   - Point out specific periods with large error spikes and explain diurnal wind variation.

4. **Daily Breakdown Table**:
   - Demonstrate sorting by MAE, RMSE, or Date.
   - Highlight the worst-performing days vs high-accuracy days.

5. **Closing & Docker Readiness**:
   - Quick reference to `docker-compose up --build` and deployment setup.
