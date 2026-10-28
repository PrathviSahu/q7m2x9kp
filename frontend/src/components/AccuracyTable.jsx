/**
 * AccuracyTable — per-day MAE, RMSE, Bias, MAPE breakdown
 */
import React, { useState, useMemo } from 'react';

const fmt = (v, d = 0) => (v == null ? '—' : Number(v).toFixed(d));
const fmtSign = (v, d = 0) => {
  if (v == null) return '—';
  return (v > 0 ? '+' : '') + Number(v).toFixed(d);
};

function biasColor(bias) {
  if (bias == null) return 'inherit';
  if (Math.abs(bias) < 50) return 'var(--accent-green)';
  if (Math.abs(bias) < 200) return 'var(--accent-amber)';
  return 'var(--accent-red)';
}

function coverageClass(coverage) {
  if (coverage >= 0.95) return 'badge-green';
  if (coverage >= 0.8) return 'badge-amber';
  return 'badge-red';
}

export function AccuracyTable({ byDate, overall }) {
  const [sortKey, setSortKey] = useState('date');
  const [sortDir, setSortDir] = useState('asc');

  const rows = useMemo(() => {
    if (!byDate) return [];
    return Object.entries(byDate).map(([date, m]) => ({ date, ...m }));
  }, [byDate]);

  const sorted = useMemo(() => {
    const dir = sortDir === 'asc' ? 1 : -1;
    return [...rows].sort((a, b) => {
      if (sortKey === 'date') return dir * a.date.localeCompare(b.date);
      const av = a[sortKey] ?? -Infinity;
      const bv = b[sortKey] ?? -Infinity;
      return dir * (av - bv);
    });
  }, [rows, sortKey, sortDir]);

  const handleSort = key => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const SortIcon = ({ k }) => {
    if (sortKey !== k) return <span style={{ opacity: 0.3 }}> ↕</span>;
    return <span> {sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div className="card" data-testid="accuracy-table">
      <div className="card-title">Daily Accuracy Breakdown</div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              {[
                ['date', 'Date'],
                ['mae_mw', 'MAE (MW)'],
                ['rmse_mw', 'RMSE (MW)'],
                ['bias_mw', 'Bias (MW)'],
                ['mape_pct', 'MAPE (%)'],
                ['matched_periods', 'Matched'],
                ['coverage', 'Coverage'],
              ].map(([k, label]) => (
                <th key={k} onClick={() => handleSort(k)} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  {label}<SortIcon k={k} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Overall summary row */}
            {overall && (
              <tr style={{ background: 'rgba(56,189,248,0.07)', fontWeight: 600 }}>
                <td>Overall</td>
                <td>{fmt(overall.mae_mw, 0)}</td>
                <td>{fmt(overall.rmse_mw, 0)}</td>
                <td style={{ color: biasColor(overall.bias_mw) }}>{fmtSign(overall.bias_mw, 0)}</td>
                <td>{fmt(overall.mape_pct, 1)}</td>
                <td>{overall.matched_periods} / {overall.total_periods}</td>
                <td><span className={`badge ${coverageClass(overall.coverage)}`}>{(overall.coverage * 100).toFixed(1)}%</span></td>
              </tr>
            )}
            {sorted.map(row => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td>{fmt(row.mae_mw, 0)}</td>
                <td>{fmt(row.rmse_mw, 0)}</td>
                <td style={{ color: biasColor(row.bias_mw) }}>{fmtSign(row.bias_mw, 0)}</td>
                <td>{fmt(row.mape_pct, 1)}</td>
                <td>{row.matched_periods} / {row.total_periods}</td>
                <td><span className={`badge ${coverageClass(row.coverage)}`}>{(row.coverage * 100).toFixed(1)}%</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

