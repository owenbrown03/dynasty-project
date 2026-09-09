import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TradeSignalsTab } from './TradeSignalsTab';

vi.mock('@/hooks/sleeper/useTrades', () => ({
  useTrades: () => ({
    data: [
      {
        transaction_id: 'tx-1',
        status: 'complete',
        type: 'trade',
        roster_ids: [1, 2],
        created: 1700000000,
        settings: null,
        league_settings: ['12 Team', 'PPR'],
      },
      {
        transaction_id: 'tx-2',
        status: 'complete',
        type: 'trade',
        roster_ids: [1, 3],
        created: 1700001000,
        settings: null,
        league_settings: ['12 Team', 'Half PPR'],
      },
    ],
    username: 'testuser',
    loading: false,
    fetching: false,
  }),
}));

vi.mock('./TradeCards', () => ({
  TradeCards: ({ trades }: { trades: unknown[] }) => (
    <div data-testid="trade-cards">Trades count: {trades.length}</div>
  ),
}));

describe('TradeSignalsTab', () => {
  it('renders pagination toolbars at both top and bottom', () => {
    render(<TradeSignalsTab />);

    expect(screen.getByText('Showing 2 of 2 trades')).toBeInTheDocument();

    const statuses = screen.getAllByText('Page 1 of 1');
    expect(statuses).toHaveLength(2);

    const prevButtons = screen.getAllByRole('button', { name: 'Previous' });
    expect(prevButtons).toHaveLength(2);

    const nextButtons = screen.getAllByRole('button', { name: 'Next' });
    expect(nextButtons).toHaveLength(2);
  });
});
