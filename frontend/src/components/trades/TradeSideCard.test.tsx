import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { describe, expect, it, vi, afterEach } from 'vitest';
import { TradeSideCard, type TradeSideAsset } from './TradeSideCard';

afterEach(() => {
  cleanup();
});

// Mock hook
vi.mock('@/hooks/sleeper/useBulkTrades', () => ({
  useBulkTradePlayerSearch: () => ({
    loading: false,
    data: [
      {
        player_id: '5012',
        name: 'Tony Pollard',
        position: 'RB',
        team: 'TEN',
        age: 29.3,
        ktc_value: 2797,
        fc_value: 2650,
      },
    ],
  }),
}));

describe('TradeSideCard', () => {
  const assets: TradeSideAsset[] = [
    {
      id: 'p-1',
      type: 'player',
      label: 'Tony Pollard',
      meta: 'RB · TEN · 29.3 y.o.',
      value: 2797,
      position: 'RB',
      team: 'TEN',
      age: 29.3,
    },
    {
      id: 'pick-1',
      type: 'pick',
      label: '2027 Round 2',
      meta: 'PICK · 12 tm · SF',
      value: 3201,
      position: 'PICK',
    },
  ];

  it('renders side title, assets with TeamBadge, and footer summary', () => {
    const handleRemove = vi.fn();
    const handleAddPlayer = vi.fn();

    render(
      <TradeSideCard
        title="Team 1 gets..."
        side="team-a"
        assets={assets}
        totalValue={5998}
        netValue={5998}
        onAddPlayer={handleAddPlayer}
        onRemoveAsset={handleRemove}
      />
    );

    expect(screen.getByText('Team 1 gets...')).toBeInTheDocument();
    expect(screen.getByText('Tony Pollard')).toBeInTheDocument();
    expect(screen.getByText('2027 Round 2')).toBeInTheDocument();
    expect(screen.getByText('2 Total Pieces')).toBeInTheDocument();
    expect(screen.getByText('1 RB, 1 Pick')).toBeInTheDocument();

    const removeBtns = screen.getAllByRole('button', { name: /Remove/i });
    expect(removeBtns.length).toBe(2);
    fireEvent.click(removeBtns[0]);
    expect(handleRemove).toHaveBeenCalledWith('p-1');
  });

  it('shows search dropdown on input change and selects player', () => {
    const handleAddPlayer = vi.fn();

    const { getByPlaceholderText, getByText } = render(
      <TradeSideCard
        title="Team 1 gets..."
        side="team-a"
        assets={[]}
        totalValue={0}
        netValue={0}
        onAddPlayer={handleAddPlayer}
        onRemoveAsset={vi.fn()}
      />
    );

    const input = getByPlaceholderText(/Search for a player/i);
    fireEvent.change(input, { target: { value: 'Tony' } });

    expect(getByText('Tony Pollard')).toBeInTheDocument();
    fireEvent.click(getByText('Tony Pollard'));

    expect(handleAddPlayer).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Tony Pollard' })
    );
  });
});
