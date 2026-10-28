/**
 * Frontend unit tests — SummaryCards and AccuracyTable components.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { SummaryCards } from './SummaryCards.jsx';
import { AccuracyTable } from './AccuracyTable.jsx';

const mockOverall = {
  mae_mw: 312.5,
  rmse_mw: 445.8,
  bias_mw: -45.2,
  mape_pct: 12.3,
  matched_periods: 1440,
  total_periods: 1488,
  coverage: 0.9677,
};

const mockByDate = {
  '2026-01-01': { mae_mw: 250, rmse_mw: 310, bias_mw: 30, mape_pct: 8.5, matched_periods: 48, total_periods: 48, coverage: 1.0 },
  '2026-01-02': { mae_mw: 380, rmse_mw: 520, bias_mw: -120, mape_pct: 15.2, matched_periods: 46, total_periods: 48, coverage: 0.9583 },
};

describe('SummaryCards', () => {
  it('renders all four KPI values', () => {
    render(<SummaryCards overall={mockOverall} />);
    expect(screen.getByTestId('summary-cards')).toBeInTheDocument();
    // MAE
    expect(screen.getByText(/MAE/)).toBeInTheDocument();
    // RMSE
    expect(screen.getByText(/RMSE/)).toBeInTheDocument();
    // Bias
    expect(screen.getByText(/Bias/)).toBeInTheDocument();
    // MAPE
    expect(screen.getByText(/MAPE/)).toBeInTheDocument();
  });

  it('shows MAE value rounded to 0 dp', () => {
    render(<SummaryCards overall={mockOverall} />);
    // 312.5 → "313" MW
    expect(screen.getByText('313')).toBeInTheDocument();
  });

  it('shows coverage matched / total', () => {
    render(<SummaryCards overall={mockOverall} />);
    expect(screen.getByText('1440')).toBeInTheDocument();
  });

  it('renders nothing when overall is null', () => {
    const { container } = render(<SummaryCards overall={null} />);
    expect(container.firstChild).toBeNull();
  });
});

describe('AccuracyTable', () => {
  it('renders the table with correct test id', () => {
    render(<AccuracyTable byDate={mockByDate} overall={mockOverall} />);
    expect(screen.getByTestId('accuracy-table')).toBeInTheDocument();
  });

  it('shows an overall summary row', () => {
    render(<AccuracyTable byDate={mockByDate} overall={mockOverall} />);
    expect(screen.getByText('Overall')).toBeInTheDocument();
  });

  it('renders a row for each date', () => {
    render(<AccuracyTable byDate={mockByDate} overall={mockOverall} />);
    expect(screen.getByText('2026-01-01')).toBeInTheDocument();
    expect(screen.getByText('2026-01-02')).toBeInTheDocument();
  });

  it('shows — for null metric values', () => {
    const sparse = { '2026-01-03': { mae_mw: null, rmse_mw: null, bias_mw: null, mape_pct: null, matched_periods: 0, total_periods: 48, coverage: 0 } };
    render(<AccuracyTable byDate={sparse} overall={null} />);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThan(0);
  });
});

