import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RecentlyDroppedTab } from './RecentlyDroppedTab';

vi.mock('@/hooks/sleeper/useConnection', () => ({
  useSleeperConnection: () => ({
    username: 'testuser',
    canWrite: true,
  }),
}));

vi.mock('@/hooks/sleeper/useWaivers', () => ({
  useRecentlyDroppedPlayers: () => ({
    data: {
      total_players: 12,
      total_pages: 2,
      page: 1,
      page_size: 10,
      value_label: 'Dynasty Value',
      value_basis: 'ktc',
      sync_requested: false,
      players: [
        {
          transaction_id: 'tx-1',
          player_id: 'p1',
          name: 'Player One',
          position: 'RB',
          team: 'KC',
          league_id: 'l1',
          league_name: 'League 1',
          league_avatar: null,
          roster_id: 1,
          roster_size: 25,
          roster_capacity: 25,
          roster_spots_available: 0,
          faab_remaining: 100,
          faab_percent_remaining: 100,
          selected_value: 1000,
          dropped_at_ms: Date.now(),
          claim_blocked_reason: null,
        },
      ],
    },
    loading: false,
    fetching: false,
  }),
}));

vi.mock('@/components/players/PlayerAvatar', () => ({
  PlayerAvatar: () => <div data-testid="player-avatar" />,
}));

vi.mock('@/components/leagues/LeagueAvatar', () => ({
  LeagueAvatar: () => <div data-testid="league-avatar" />,
}));

vi.mock('@/components/players/TeamBadge', () => ({
  TeamBadge: () => <div data-testid="team-badge" />,
}));

describe('RecentlyDroppedTab', () => {
  it('renders pagination toolbars at both top and bottom', () => {
    render(<RecentlyDroppedTab valueBasis="ktc" />);

    const statuses = screen.getAllByText('Page 1 of 2');
    expect(statuses).toHaveLength(2);

    const prevButtons = screen.getAllByRole('button', { name: 'Previous' });
    expect(prevButtons).toHaveLength(2);

    const nextButtons = screen.getAllByRole('button', { name: 'Next' });
    expect(nextButtons).toHaveLength(2);

    const sortLabels = screen.getAllByLabelText('Sort');
    expect(sortLabels).toHaveLength(2);
  });
});
