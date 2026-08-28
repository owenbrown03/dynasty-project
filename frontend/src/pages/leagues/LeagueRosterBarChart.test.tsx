import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { LeagueDetails, LeagueRoster } from '@/types';
import { LeagueRosterBarChart } from './LeagueRosterBarChart';

afterEach(() => {
  cleanup();
});

vi.mock('@/hooks/useBootstrap', () => ({
  useBootstrap: () => ({
    data: {
      sleeper: {
        sleeper_user_id: 'user-1',
      },
    },
  }),
}));

const mockRoster1: LeagueRoster = {
  roster_id: 1,
  owner: {
    user_id: 'user-1',
    display_name: 'Alpha Squad',
    avatar: null,
  },
  record: '6-2',
  wins: 6,
  losses: 2,
  ties: 0,
  actual_points_for: 1100.5,
  projected_points: 220.3,
  faab_remaining: 80,
  waiver_position: 1,
  total_moves: 10,
  total_trades: 4,
  open_roster_spots: 2,
  average_age: 24.5,
  total_ktc_value: 15000,
  total_fc_value: 14000,
  total_redraft_starter_war: 5.2,
  total_redraft_roster_war: 7.1,
  total_dynasty_starter_war: 8.5,
  total_dynasty_roster_war: 12.4,
  total_pick_ktc_value: 3000,
  total_pick_fc_value: 2800,
  total_pick_rookie_war_value: 3.5,
  total_asset_ktc_value: 18000,
  total_asset_fc_value: 16800,
  stat_ranks: {},
  rank: 1,
  players: [],
  picks: [],
};

const mockRoster2: LeagueRoster = {
  roster_id: 2,
  owner: {
    user_id: 'user-2',
    display_name: 'Beta Titans',
    avatar: null,
  },
  record: '3-5',
  wins: 3,
  losses: 5,
  ties: 0,
  actual_points_for: 950.0,
  projected_points: 190.0,
  faab_remaining: 45,
  waiver_position: 5,
  total_moves: 20,
  total_trades: 8,
  open_roster_spots: 0,
  average_age: 27.2,
  total_ktc_value: 20000,
  total_fc_value: 19000,
  total_redraft_starter_war: 3.1,
  total_redraft_roster_war: 4.5,
  total_dynasty_starter_war: 10.2,
  total_dynasty_roster_war: 15.0,
  total_pick_ktc_value: 1000,
  total_pick_fc_value: 900,
  total_pick_rookie_war_value: 1.0,
  total_asset_ktc_value: 21000,
  total_asset_fc_value: 19900,
  stat_ranks: {},
  rank: 2,
  players: [],
  picks: [],
};

const mockLeague: LeagueDetails = {
  league_id: 'league-123',
  league_name: 'Dynasty Championship',
  avatar: null,
  season: '2026',
  total_rosters: 2,
  roster_positions: ['QB', 'RB', 'WR', 'TE'],
  roster_construction_targets: [],
  note: '',
  draft_pick_projection_summary: null,
  war_position_history: [],
  war_player_history: [],
  settings_badges: [],
  settings_details: [],
  rosters: [mockRoster1, mockRoster2],
};

describe('LeagueRosterBarChart', () => {
  it('renders bar chart with team names, stats, and highlights user team', () => {
    render(<LeagueRosterBarChart league={mockLeague} />);

    expect(screen.getByText(/Dynasty Roster WAR by Roster/i)).toBeInTheDocument();
    expect(screen.getByText('Alpha Squad')).toBeInTheDocument();
    expect(screen.getByText('Beta Titans')).toBeInTheDocument();
    expect(screen.getByText('You')).toBeInTheDocument();

    // Default Dynasty WAR: Beta Titans (15.00) is #1, Alpha Squad (12.40) is #2
    const rows = screen.getAllByRole('listitem');
    expect(rows[0]).toHaveTextContent('Beta Titans');
    expect(rows[0]).toHaveTextContent('15.00 WAR');
    expect(rows[1]).toHaveTextContent('Alpha Squad');
    expect(rows[1]).toHaveTextContent('12.40 WAR');
    expect(rows[1]).toHaveClass('is-user-team');
  });

  it('changes metric via select dropdown and re-sorts the rosters', () => {
    render(<LeagueRosterBarChart league={mockLeague} />);

    const select = screen.getByLabelText('Select stat metric');
    fireEvent.change(select, { target: { value: 'redraft_roster_war' } });

    expect(screen.getByText(/Redraft Roster WAR by Roster/i)).toBeInTheDocument();

    // Redraft WAR: Alpha Squad (7.10) > Beta Titans (4.50)
    const rows = screen.getAllByRole('listitem');
    expect(rows[0]).toHaveTextContent('Alpha Squad');
    expect(rows[0]).toHaveTextContent('7.10 WAR');
    expect(rows[1]).toHaveTextContent('Beta Titans');
    expect(rows[1]).toHaveTextContent('4.50 WAR');
  });

  it('updates sort direction when sort order is changed', () => {
    render(<LeagueRosterBarChart league={mockLeague} />);

    const sortSelect = screen.getByLabelText('Select sort order');
    fireEvent.change(sortSelect, { target: { value: 'asc' } });

    // In ascending order for Dynasty WAR: Alpha Squad (12.40) comes first, then Beta Titans (15.00)
    const rows = screen.getAllByRole('listitem');
    expect(rows[0]).toHaveTextContent('Alpha Squad');
    expect(rows[1]).toHaveTextContent('Beta Titans');
  });

  it('displays summary metrics for the selected stat', () => {
    render(<LeagueRosterBarChart league={mockLeague} />);

    expect(screen.getByText('Leader / Top')).toBeInTheDocument();
    expect(screen.getByText('League Avg')).toBeInTheDocument();
    expect(screen.getByText('Your Team')).toBeInTheDocument();
  });
});
