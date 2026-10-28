/**
 * SummaryCards — four KPI cards: MAE, RMSE, Bias, Coverage
 */
import React from 'react';

function badge(bias) {
  if (bias === null || bias === undefined) return null;
  if (Math.abs(bias) < 50) return { cls: 'badge-green', label: 'Low bias' };
  if (Math.abs(bias) < 200) return { cls: 'badge-amber', label: bias > 0 ? 'Over-forecast' : 'Under-forecast' };
  return { cls: 'badge-red', label: bias > 0 ? 'Over-forecast' : 'Under-forecast' };
}

export function SummaryCards({ overall }) {
  if (!overall) return null;
  const biasBadge = badge(overall.bias_mw);
  const fmt = (v, d = 0) => (v == null ? '—' : Number(v).toFixed(d));

  return (
    <div className="kpi-grid" data-testid="summary-cards">
      <div className="card">
        <div className="card-title">MAE</div>
        <div className="kpi-value">
          {fmt(overall.mae_mw, 0)}<span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-label">Mean Absolute Error</div>
      </div>

      <div className="card">
        <div className="card-title">RMSE</div>
        <div className="kpi-value">
          {fmt(overall.rmse_mw, 0)}<span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-label">Root Mean Square Error</div>
      </div>

      <div className="card">
        <div className="card-title">Bias</div>
        <div className="kpi-value" style={{ color: overall.bias_mw > 0 ? 'var(--accent-amber)' : 'var(--accent-blue)' }}>
          {overall.bias_mw != null && overall.bias_mw > 0 ? '+' : ''}{fmt(overall.bias_mw, 0)}<span className="kpi-unit">MW</span>
        </div>
        {biasBadge && (
          <div className="kpi-label">
            <span className={`badge ${biasBadge.cls}`}>{biasBadge.label}</span>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">MAPE</div>
        <div className="kpi-value">
          {fmt(overall.mape_pct, 1)}<span className="kpi-unit">%</span>
        </div>
        <div className="kpi-label">Mean Abs % Error (≥50 MW actual)</div>
      </div>

      <div className="card">
        <div className="card-title">Coverage</div>
        <div className="kpi-value">
          {overall.matched_periods ?? '—'}<span className="kpi-unit"> / {overall.total_periods ?? '—'}</span>
        </div>
        <div className="kpi-label">
          Matched periods ({overall.coverage != null ? (overall.coverage * 100).toFixed(1) : '—'}%)
        </div>
      </div>
    </div>
  );
}

