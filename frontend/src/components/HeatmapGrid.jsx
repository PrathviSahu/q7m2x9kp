/**
 * HeatmapGrid — 31 rows (days) × 48 cols (periods), colour = |error_mw|
 * Helps visualise which days / times of day had the worst forecast errors.
 */
import React, { useMemo } from 'react';

// Colour scale: white (no error) → amber → red (large error)
function errorColor(absError, maxError) {
  if (absError == null) return '#1e293b'; // no data
  const t = Math.min(absError / maxError, 1);
  if (t < 0.5) {
    // white → amber
    const r = Math.round(255 - (255 - 251) * t * 2);
    const g = Math.round(255 - (255 - 191) * t * 2);
    const b = Math.round(255 - (255 - 36) * t * 2);
    return `rgb(${r},${g},${b})`;
  } else {
    // amber → red
    const s = (t - 0.5) * 2;
    const r = Math.round(251 + (248 - 251) * s);
    const g = Math.round(191 - (191 - 113) * s);
    const b = Math.round(36 - (36 - 113) * s);
    return `rgb(${r},${g},${b})`;
  }
}

export function HeatmapGrid({ series }) {
  const { grid, dates, maxError } = useMemo(() => {
    if (!series?.length) return { grid: {}, dates: [], maxError: 0 };

    // Build map: date → { period → absError }
    const map = {};
    let max = 0;
    for (const r of series) {
      if (!map[r.settlementDate]) map[r.settlementDate] = {};
      const abs = r.error_mw != null ? Math.abs(r.error_mw) : null;
      map[r.settlementDate][r.settlementPeriod] = abs;
      if (abs != null && abs > max) max = abs;
    }
    const dates = Object.keys(map).sort();
    return { grid: map, dates, maxError: max || 1 };
  }, [series]);

  const periods = Array.from({ length: 48 }, (_, i) => i + 1);

  return (
    <div className="card" data-testid="heatmap-grid">
      <div className="card-title">Forecast Error Heatmap — |Error| MW per Settlement Period</div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>
        Rows = days (Jan 1 → Jan 31) · Columns = settlement periods (1–48, 00:00–23:30 UTC) · Darker = larger absolute error
      </div>
      <div className="heatmap-scroll">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 4 }}>
          {/* Day labels */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingTop: 2 }}>
            {dates.map(d => (
              <div key={d} style={{ height: 14, fontSize: 9, color: 'var(--text-muted)', lineHeight: '14px', width: 42 }}>
                {d.slice(5)}
              </div>
            ))}
          </div>
          {/* Grid */}
          <div>
            <div style={{ display: 'flex', gap: 2, marginBottom: 2 }}>
              {[1, 12, 24, 36, 48].map(p => (
                <div key={p} style={{
                  fontSize: 9, color: 'var(--text-muted)',
                  width: 14, textAlign: 'center',
                  marginLeft: p === 1 ? 0 : `${(p - (p === 12 ? 1 : p === 24 ? 12 : p === 36 ? 24 : p === 48 ? 36 : 0) - 1) * 16}px`,
                }}>
                  {p}
                </div>
              ))}
            </div>
            {dates.map(d => (
              <div key={d} style={{ display: 'flex', gap: 2, marginBottom: 2 }}>
                {periods.map(p => {
                  const val = grid[d]?.[p];
                  return (
                    <div
                      key={p}
                      className="heatmap-cell"
                      title={`${d} P${p}: ${val != null ? Math.round(val) + ' MW error' : 'no data'}`}
                      style={{ background: errorColor(val, maxError) }}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="heatmap-legend">
        <span>Low error</span>
        {[0, 0.25, 0.5, 0.75, 1].map(t => (
          <div key={t} style={{
            width: 16, height: 10, borderRadius: 2,
            background: errorColor(t * maxError, maxError),
            border: '1px solid rgba(255,255,255,0.1)',
          }} />
        ))}
        <span>High error ({Math.round(maxError)} MW)</span>
      </div>
    </div>
  );
}

