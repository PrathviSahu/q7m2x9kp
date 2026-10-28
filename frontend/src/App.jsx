/**
 * App — root component. Wires data hook to chart/table/heatmap views.
 */
import React, { useState } from 'react';
import { Wind, RefreshCw, AlertCircle } from 'lucide-react';
import { useWindData } from './hooks/useWindData.js';
import { SummaryCards } from './components/SummaryCards.jsx';
import { TimeSeriesChart } from './components/TimeSeriesChart.jsx';
import { AccuracyTable } from './components/AccuracyTable.jsx';
import { HeatmapGrid } from './components/HeatmapGrid.jsx';

const TABS = [
  { id: 'chart', label: 'Time Series' },
  { id: 'heatmap', label: 'Error Heatmap' },
  { id: 'table', label: 'Daily Breakdown' },
];

export default function App() {
  const [tab, setTab] = useState('chart');
  const { data, loading, error, refetch } = useWindData('2026-01-01', '2026-01-31');

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <Wind size={22} color="var(--accent-blue)" />
        <div>
          <h1>UK Wind Forecast Dashboard</h1>
          <div className="subtitle">
            Day-ahead forecast accuracy · January 2026 · Elexon BMRS (FUELHH + WINDFOR)
          </div>
        </div>
        <button
          onClick={refetch}
          disabled={loading}
          title="Reload data"
          style={{
            marginLeft: 'auto', background: 'none', border: '1px solid var(--border)',
            borderRadius: 6, padding: '0.3rem 0.7rem', color: 'var(--text-muted)',
            cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 4,
          }}
        >
          <RefreshCw size={14} style={{ animation: loading ? 'spin 0.8s linear infinite' : 'none' }} />
          <span style={{ fontSize: 12 }}>Refresh</span>
        </button>
      </header>

      <main className="main">
        {/* Error Banner */}
        {error && (
          <div className="error-box" role="alert">
            <AlertCircle size={16} style={{ verticalAlign: 'middle', marginRight: 6 }} />
            <strong>Could not load data:</strong> {error}
            <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)' }}>
              Make sure the backend is running on port 8000 and the Elexon API is accessible.
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="loading">
            <span className="spinner" />
            Fetching January 2026 wind data from Elexon BMRS…
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
              This makes two API calls (FUELHH + WINDFOR) covering 1,488 settlement periods.
              Expect 5–15 seconds on first load.
            </div>
          </div>
        )}

        {/* Main content */}
        {!loading && data && (
          <>
            <SummaryCards overall={data.overall} />

            <div className="tab-row">
              {TABS.map(t => (
                <button
                  key={t.id}
                  className={`tab-btn ${tab === t.id ? 'active' : ''}`}
                  onClick={() => setTab(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {tab === 'chart' && <TimeSeriesChart series={data.series} />}
            {tab === 'heatmap' && <HeatmapGrid series={data.series} />}
            {tab === 'table' && <AccuracyTable byDate={data.by_date} overall={data.overall} />}

            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 16 }}>
              Data: Elexon Insights Solution API · FUELHH (actual generation) + WINDFOR (NG ESO forecasts) ·
              Day-ahead cutoff: last WINDFOR run published before 11:00 UTC on D-1 ·
              Metrics exclude periods with missing actual or forecast data.
            </div>
          </>
        )}
      </main>
    </div>
  );
}

