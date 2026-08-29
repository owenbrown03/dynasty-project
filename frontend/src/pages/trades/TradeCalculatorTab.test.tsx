import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TradeCalculatorTab } from './TradeCalculatorTab';

vi.mock('@/context/useValuePreference', () => ({
  useValuePreference: () => ({
    valuePreference: 'ktc',
    setValuePreference: vi.fn(),
  }),
}));

vi.mock('@/hooks/sleeper/useBulkTrades', () => ({
  useBulkTradePlayerSearch: () => ({
    loading: false,
    data: [],
  }),
  fetchTradeCalculatorPickValue: vi.fn(),
}));

describe('TradeCalculatorTab', () => {
  it('renders KTC-style trade calculator layout with two side cards and winning meter', () => {
    render(<TradeCalculatorTab />);

    expect(screen.getByText('Trade Calculator')).toBeInTheDocument();
    expect(screen.getByText('Team 1 gets...')).toBeInTheDocument();
    expect(screen.getByText('Team 2 gets...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: /Trade balance meter/i })).toBeInTheDocument();
    expect(screen.getByText(/Send to Bulk Offers/i)).toBeInTheDocument();
  });
});
