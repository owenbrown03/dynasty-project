import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { vi } from 'vitest';

import { LeagueCard } from './LeagueCard';
import type { LeagueDetails } from '@/types';

vi.mock('@/hooks/sleeper/useLeagues', () => ({
  useSaveUserNote: () => ({
    saveNote: vi.fn(),
    saving: false,
  }),
}));

vi.mock('@/utils/notify', () => ({
  notify: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));


const league: LeagueDetails = {
  league_id: 'league-1',
  league_name: 'Test League',
  avatar: null,
  season: '2026',
  total_rosters: 12,
  roster_positions: ['QB', 'RB', 'WR', 'TE', 'FLEX', 'BN'],
  roster_construction_targets: [
    { position: 'QB', target_count: 3, war_share: 28.4 },
    { position: 'RB', target_count: 8, war_share: 24.1 },
    { position: 'WR', target_count: 9, war_share: 38.6 },
    { position: 'TE', target_count: 2, war_share: 8.9 },
  ],
  note: '',
  draft_pick_projection_summary: null,
  war_position_history: [],
  war_player_history: [],
  settings_badges: ['Best Ball', '12 Team'],
  settings_details: [
    { label: 'Season', value: '2026' },
    { label: 'Format', value: 'Superflex' },
  ],
  rosters: [
    {
      roster_id: 1,
      owner: {
        user_id: 'user-1',
        display_name: 'Alpha',
        avatar: null,
      },
      record: '5-1',
      wins: 5,
      losses: 1,
      ties: 0,
      actual_points_for: 901.5,
      projected_points: 210.4,
      faab_remaining: 75,
      waiver_position: 3,
      total_trades: 10,
      open_roster_spots: 1,
      average_age: 25.6,
      total_ktc_value: 1000,
      total_fc_value: 900,
      total_redraft_starter_war: 4,
      total_redraft_roster_war: 6,
      total_dynasty_starter_war: 8,
      total_dynasty_roster_war: 9,
      total_pick_ktc_value: 200,
      total_pick_fc_value: 150,
      total_pick_rookie_war_value: 12.5,
      total_asset_ktc_value: 1200,
      total_asset_fc_value: 1050,
      stat_ranks: {},
      rank: 1,
      players: [],
      picks: [],
    },
  ],
};


describe('LeagueCard', () => {
  it('renders league settings and roster ownership summary', () => {
    render(
      <LeagueCard
        league={league}
        rosterSortBasis="ktc"
        warValueSettings={{
          sleeper_projection: {
            timeframe: 'dynasty',
            scope: 'roster',
          },
          my: {
            timeframe: 'dynasty',
            scope: 'roster',
          },
        }}
      />,
    );

    expect(
      screen.getByText('Test League'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('League settings'),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /alpha/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Best Ball'),
    ).toBeInTheDocument();
  });
});
