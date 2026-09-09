import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AvailablePlayersTab } from './AvailablePlayersTab';

vi.mock('@/hooks/sleeper/useConnection', () => ({
  useSleeperConnection: () => ({
    username: 'testuser',
    canWrite: true,
  }),
}));

vi.mock('@/hooks/sleeper/useWaivers', () => ({
  useWaiverLeagueOptions: () => ({
    data: [
      { league_id: 'league-1', league_name: 'League 1' },
    ],
    loading: false,
  }),
  useAvailableWaiverPlayers: () => ({
    data: {
      is_all_leagues: false,
      total_players: 25,
      total_pages: 3,
      page: 1,
      page_size: 10,
      value_label: 'Dynasty Value',
      value_basis: 'ktc',
      players: [],
    },
    loading: false,
    fetching: false,
    error: null,
  }),
}));

vi.mock('./AvailablePlayersTable', () => ({
  AvailablePlayersTable: () => <div data-testid="available-players-table" />,
}));

vi.mock('./AvailableLeagueSelector', () => ({
  AvailableLeagueSelector: () => <div data-testid="available-league-selector" />,
}));

describe('AvailablePlayersTab', () => {
  it('renders pagination toolbars at both top and bottom', () => {
    render(
      <AvailablePlayersTab
        valueBasis="ktc"
        selectedLeagueId="league-1"
        onSelectedLeagueIdChange={vi.fn()}
      />,
    );

    const statuses = screen.getAllByText('Page 1 of 3');
    expect(statuses).toHaveLength(2);

    const prevButtons = screen.getAllByRole('button', { name: 'Previous' });
    expect(prevButtons).toHaveLength(2);

    const nextButtons = screen.getAllByRole('button', { name: 'Next' });
    expect(nextButtons).toHaveLength(2);
  });
});
