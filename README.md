# UK Wind Generation Forecast & Accuracy Dashboard

An interactive full-stack dashboard analysing UK wind generation forecasts vs outturn across **January 2026**, built with **React + Vite** and **Python (FastAPI)**.

- **Live Dashboard (Vercel):** [https://q7m2x9kp-two.vercel.app](https://q7m2x9kp-two.vercel.app)
- **Live Backend API (Render):** [https://wind-forecast-zhc3.onrender.com](https://wind-forecast-zhc3.onrender.com)
- **Interactive Swagger Docs:** [https://wind-forecast-zhc3.onrender.com/docs](https://wind-forecast-zhc3.onrender.com/docs)
- **Public GitHub Repository:** [https://github.com/PrathviSahu/q7m2x9kp](https://github.com/PrathviSahu/q7m2x9kp)

Data is sourced from the official **Elexon Insights Solution (BMRS)** REST API:
- **`FUELHH`**: Half-hourly generation outturn by fuel type (wind offshore + onshore outturn in MW).
- **`WINDFOR`**: National Grid ESO wind generation forecasts (MW).

---

## Verified January 2026 Results

| Metric | Value | Description |
|---|---|---|
| **Matched Intervals** | **1,488 / 1,488** | 100% complete coverage across all 31 days (31 × 48 half-hours) |
| **MAE** | **2,126.12 MW** | Mean Absolute Error across all settlement intervals |
| **RMSE** | **2,620.80 MW** | Root Mean Square Error (penalising large forecast deviations) |
| **Signed Bias** | **+1,840.30 MW** | Net positive bias (systematic over-forecast across 1,252 periods) |
| **MAPE** | **22.13%** | Mean Absolute Percentage Error (for intervals with actual $\ge 50$ MW) |

---

## Key Highlights & Methodology

1. **Strict Day-Ahead Cutoff (Zero Future-Data Leakage)**:
   - For any delivery day $D$, electricity market day-ahead gate closure occurs at **11:00 UTC on $D-1$** (EPEX / N2EX GB standard).
   - The application strictly queries forecasts published on or before **10:59 UTC on $D-1$** and selects the latest available run (typically the 09:30 UTC publication).
   - Intraday iterations published after 11:00 UTC are strictly excluded to avoid look-ahead bias and accurately reflect the market participant's decision state.

2. **Settlement Period Mapping & Granularity**:
   - GB electricity settlement operates on 30-minute intervals (48 settlement periods per day, starting at 23:00 UTC of the preceding calendar day during winter).
   - WINDFOR forecasts are published at hourly intervals ($24$ records per day). Since MW is an average power rate, each hourly forecast is mapped to both corresponding half-hour settlement periods ($p$ and $p+1$).
   - FUELHH provides all 48 settlement periods. Across all 31 days of January 2026, all **1,488 half-hour settlement periods** are evaluated.

3. **Forecast Accuracy Metrics**:
   - **MAE** (Mean Absolute Error): $\frac{1}{N}\sum | \hat{y}_i - y_i |$
   - **RMSE** (Root Mean Square Error): $\sqrt{\frac{1}{N}\sum (\hat{y}_i - y_i)^2}$
   - **Bias** (Mean Error): $\frac{1}{N}\sum (\hat{y}_i - y_i)$ (positive indicates systematic over-forecasting)
   - **MAPE** (Mean Absolute Percentage Error): computed only where actual $y_i \ge 50$ MW to prevent zero-division inflation.
   - **Coverage & Missing Data**: Periods with missing actuals or forecasts are marked `null`, excluded from error denominators, and reported via a completeness percentage.

---

## Project Structure

```
wind-forecast-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & CORS
│   │   ├── models.py            # Pydantic data schemas
│   │   ├── routers/
│   │   │   └── wind.py          # /api/wind endpoints + in-memory TTL caching
│   │   └── services/
│   │       ├── elexon.py        # Elexon BMRS client (FUELHH + WINDFOR stream)
│   │       └── analysis.py      # Accuracy metric calculation engine
│   ├── tests/
│   │   ├── test_analysis.py     # Unit tests for metrics & edge cases
│   │   ├── test_elexon.py       # Cutoff logic & settlement mapping tests
│   │   └── test_api.py          # API route integration tests
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main dashboard view & tabs
│   │   ├── components/
│   │   │   ├── SummaryCards.jsx # Top-level KPI cards (MAE, RMSE, Bias, MAPE, Coverage)
│   │   │   ├── TimeSeriesChart.jsx # Recharts actual vs forecast line chart
│   │   │   ├── HeatmapGrid.jsx  # 31 x 48 error heatmap matrix
│   │   │   ├── AccuracyTable.jsx# Sortable daily accuracy table
│   │   │   └── components.test.jsx # React Testing Library component tests
│   │   ├── hooks/
│   │   │   └── useWindData.js   # Data fetching hook
│   │   ├── styles/
│   │   │   └── index.css        # Clean dark-mode dashboard styling
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf               # Production Nginx reverse-proxy
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml           # Unified orchestration
├── .github/workflows/ci.yml     # Automated CI for backend & frontend
└── README.md
```

---

## Quickstart (Local Development)

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (optional)

### 1. Run with Docker Compose
```bash
docker-compose up --build
```
- Dashboard: [http://localhost:3000](http://localhost:3000)
- Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Manual Setup (Without Docker)

#### Backend:
```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

---

## Running Tests

### Backend Tests (pytest)
```bash
cd backend
.venv/bin/pytest tests/ -v
```
Output:
```text
======================== 30 passed in 1.03s =========================
```

### Frontend Tests (vitest)
```bash
cd frontend
npm test
```
Output:
```text
✓ src/components/components.test.jsx (8)
Test Files  1 passed (1)
     Tests  8 passed (8)
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `GET` | `/api/wind/actuals` | Half-hourly actual wind generation (`FUELHH`) |
| `GET` | `/api/wind/forecasts` | Day-ahead wind forecasts with gate closure cutoff (`WINDFOR`) |
| `GET` | `/api/wind/accuracy` | Joined time series + overall & daily MAE, RMSE, Bias, MAPE |

Query Parameters for `/api/wind/*`:
- `date_from` (default: `2026-01-01`)
- `date_to` (default: `2026-01-31`)
- `refresh` (boolean, bypasses server cache)

---

## Deployment Guide

### Frontend (Vercel)
1. Import repository on [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Add Environment Variable:
   - `VITE_API_BASE_URL`: URL of the deployed FastAPI backend (e.g. `https://your-api.onrender.com`).
4. Deploy!

### Backend (Render or Heroku)
- **Render**: Connect repository, set Root Directory to `backend`, Build Command: `pip install -r requirements.txt`, Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Heroku / Container**: Build and deploy `backend/Dockerfile` with `PORT` binding.
