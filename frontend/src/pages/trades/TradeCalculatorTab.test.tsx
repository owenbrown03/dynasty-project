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

vi.mock('@/hooks/sleeper/useConnection', () => ({
  useSleeperConnection: () => ({
    canWrite: true,
    connection: null,
  }),
}));

vi.mock('@/hooks/sleeper/useAuth', () => ({
  useSleeperAuth: () => ({
    openModal: vi.fn(),
  }),
}));

describe('TradeCalculatorTab', () => {
  it('renders KTC-style trade calculator layout with two side cards, winning meter, and value basis dropdown with WAR options', () => {
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
    expect(screen.getByRole('option', { name: /Dynasty WAR \(Starters\)/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Dynasty WAR \(Full Roster\)/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Redraft WAR \(Starters\)/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Redraft WAR \(Full Roster\)/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /My Dynasty WAR/i })).toBeInTheDocument();

    fireEvent.change(basisSelect, { target: { value: 'dynasty_starter_war' } });
    expect(mockSetPreference).toHaveBeenCalledWith('dynasty_starter_war');
  });

  it('renders login banner when user does not have write access', async () => {
    const { useSleeperConnection } = await import('@/hooks/sleeper/useConnection');
    const { useSleeperAuth } = await import('@/hooks/sleeper/useAuth');
    vi.mocked(useSleeperConnection).mockReturnValue({
      canWrite: false,
      connection: null,
    } as never);

    const mockOpen = vi.fn();
    vi.mocked(useSleeperAuth).mockReturnValue({
      openModal: mockOpen,
    } as never);

    render(<TradeCalculatorTab />);

    expect(screen.getByText('Trade Execution')).toBeInTheDocument();
    const loginButton = screen.getByRole('button', { name: /Log In for Write Access/i });
    expect(loginButton).toBeInTheDocument();

    fireEvent.click(loginButton);
    expect(mockOpen).toHaveBeenCalled();
  });
});
