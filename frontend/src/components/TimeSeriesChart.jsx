/**
 * TimeSeriesChart — actual vs day-ahead forecast line chart (Recharts)
 * Renders the full January 2026 half-hourly timeseries.
 */
import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

function formatXAxis(startTime) {
  if (!startTime) return '';
  const d = new Date(startTime);
  return d.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' });
}

function formatTooltipLabel(startTime) {
  if (!startTime) return '';
  const d = new Date(startTime);
  return d.toLocaleString('en-GB', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
    timeZone: 'UTC',
  }) + ' UTC';
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const actual = payload.find(p => p.dataKey === 'actual_mw');
  const forecast = payload.find(p => p.dataKey === 'forecast_mw');
  const error = actual?.value != null && forecast?.value != null
    ? (forecast.value - actual.value).toFixed(0)
    : null;
  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)',
      borderRadius: 6, padding: '8px 12px', fontSize: 12,
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{formatTooltipLabel(label)}</div>
      {actual && <div style={{ color: '#38bdf8' }}>Actual: <b>{actual.value?.toFixed(0)} MW</b></div>}
      {forecast && <div style={{ color: '#4ade80' }}>Forecast: <b>{forecast.value?.toFixed(0)} MW</b></div>}
      {error !== null && (
        <div style={{ color: Number(error) > 0 ? 'var(--accent-amber)' : 'var(--accent-blue)', marginTop: 4 }}>
          Error: {Number(error) > 0 ? '+' : ''}{error} MW
        </div>
      )}
    </div>
  );
};

export function TimeSeriesChart({ series }) {
  // Downsample for rendering performance: show every 2nd point (still 744 pts)
  const data = useMemo(() => {
    if (!series) return [];
    return series.filter((_, i) => i % 2 === 0).map(r => ({
      startTime: r.startTime,
      actual_mw: r.actual_mw,
      forecast_mw: r.forecast_mw,
    }));
  }, [series]);

  // Tick every ~3 days ≈ every 144 HH periods → ~72 after downsampling
  const tickInterval = Math.floor(data.length / 10);

  return (
    <div className="card chart-container" data-testid="timeseries-chart">
      <div className="card-title">Actual vs Day-Ahead Forecast — January 2026</div>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="startTime"
            tickFormatter={formatXAxis}
            interval={tickInterval}
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            axisLine={{ stroke: 'var(--border)' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={v => `${(v / 1000).toFixed(0)}GW`}
            width={44}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 12, color: 'var(--text-muted)' }}
            formatter={v => v === 'actual_mw' ? 'Actual' : 'DA Forecast'}
          />
          <Line
            type="monotone"
            dataKey="actual_mw"
            stroke="#38bdf8"
            strokeWidth={1.5}
            dot={false}
            name="actual_mw"
          />
          <Line
            type="monotone"
            dataKey="forecast_mw"
            stroke="#4ade80"
            strokeWidth={1.5}
            dot={false}
            strokeDasharray="4 2"
            name="forecast_mw"
          />
        </LineChart>
      </ResponsiveContainer>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
        Forecast = last WINDFOR run published before 11:00 UTC on D-1 (day-ahead gate cutoff). Times in UTC.
      </div>
    </div>
  );
}

