import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TradeCalculatorTab } from './TradeCalculatorTab';

const mockSetPreference = vi.fn();

vi.mock('@/context/useValuePreference', () => ({
  useValuePreference: () => ({
    preference: 'ktc',
    setPreference: mockSetPreference,
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
  it('renders KTC-style trade calculator layout with two side cards, winning meter, and value basis dropdown', () => {
    render(<TradeCalculatorTab />);

    expect(screen.getByText('Trade Calculator')).toBeInTheDocument();
    expect(screen.getByText('Team 1 gets...')).toBeInTheDocument();
    expect(screen.getByText('Team 2 gets...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: /Trade balance meter/i })).toBeInTheDocument();
    expect(screen.getByText(/Send to Bulk Offers/i)).toBeInTheDocument();

    const basisSelect = screen.getByRole('combobox', { name: /Value basis/i });
    expect(basisSelect).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /KeepTradeCut \(KTC\)/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /FantasyCalc \(FC\)/i })).toBeInTheDocument();

    fireEvent.change(basisSelect, { target: { value: 'fantasycalc' } });
    expect(mockSetPreference).toHaveBeenCalledWith('fantasycalc');
  });
});
