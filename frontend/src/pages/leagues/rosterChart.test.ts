import { describe, expect, it } from 'vitest';
import type { LeagueDetails, LeagueRoster } from '@/types';
import {
  computeRosterStatSummary,
  formatRosterStatValue,
  getRosterStatValue,
  ROSTER_STAT_OPTIONS,
  sortRostersByStat,
} from './rosterChart';

const mockRoster1: LeagueRoster = {
  roster_id: 1,
  owner: {
    user_id: 'user-1',
    display_name: 'Team Alpha',
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
    display_name: 'Team Beta',
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

describe('rosterChart utilities', () => {
  it('defines all required stat options with groups and labels', () => {
    expect(ROSTER_STAT_OPTIONS.length).toBeGreaterThanOrEqual(15);
    const keys = ROSTER_STAT_OPTIONS.map((o) => o.key);
    expect(keys).toContain('dynasty_roster_war');
    expect(keys).toContain('redraft_roster_war');
    expect(keys).toContain('projected_points');
    expect(keys).toContain('total_asset_ktc_value');
    expect(keys).toContain('total_asset_fc_value');
    expect(keys).toContain('pick_rookie_war');
    expect(keys).toContain('average_age');
    expect(keys).toContain('open_roster_spots');
  });

  it('correctly extracts stat values for each key', () => {
    expect(getRosterStatValue(mockRoster1, 'dynasty_roster_war')).toBe(12.4);
    expect(getRosterStatValue(mockRoster1, 'redraft_roster_war')).toBe(7.1);
    expect(getRosterStatValue(mockRoster1, 'projected_points')).toBe(220.3);
    expect(getRosterStatValue(mockRoster1, 'total_asset_ktc_value')).toBe(18000);
    expect(getRosterStatValue(mockRoster1, 'total_asset_fc_value')).toBe(16800);
    expect(getRosterStatValue(mockRoster1, 'pick_rookie_war')).toBe(3.5);
    expect(getRosterStatValue(mockRoster1, 'average_age')).toBe(24.5);
    expect(getRosterStatValue(mockRoster1, 'open_roster_spots')).toBe(2);
    expect(getRosterStatValue(mockRoster1, 'wins')).toBe(6);
    expect(getRosterStatValue(mockRoster1, 'faab_remaining')).toBe(80);
    expect(getRosterStatValue(mockRoster1, 'total_moves')).toBe(10);
    expect(getRosterStatValue(mockRoster1, 'total_trades')).toBe(4);
  });

  it('formats stat values cleanly', () => {
    expect(formatRosterStatValue(12.4, 'dynasty_roster_war')).toBe('12.40 WAR');
    expect(formatRosterStatValue(18000, 'total_asset_ktc_value')).toBe('18,000 KTC');
    expect(formatRosterStatValue(16800, 'total_asset_fc_value')).toBe('16,800 FC');
    expect(formatRosterStatValue(220.34, 'projected_points')).toBe('220.3 pts');
    expect(formatRosterStatValue(6, 'wins')).toBe('6 wins');
    expect(formatRosterStatValue(1, 'wins')).toBe('1 win');
    expect(formatRosterStatValue(24.5, 'average_age')).toBe('24.5 yrs');
    expect(formatRosterStatValue(2, 'open_roster_spots')).toBe('2 spots');
    expect(formatRosterStatValue(80, 'faab_remaining')).toBe('$80');
    expect(formatRosterStatValue(null, 'average_age')).toBe('—');
  });

  it('sorts rosters descending and ascending by chosen stat', () => {
    // Dynasty Roster WAR: Team Beta (15.0) > Team Alpha (12.4)
    const sortedDesc = sortRostersByStat(
      [mockRoster1, mockRoster2],
      'dynasty_roster_war',
      'desc',
    );
    expect(sortedDesc[0].roster_id).toBe(2);
    expect(sortedDesc[1].roster_id).toBe(1);

    const sortedAsc = sortRostersByStat(
      [mockRoster1, mockRoster2],
      'dynasty_roster_war',
      'asc',
    );
    expect(sortedAsc[0].roster_id).toBe(1);
    expect(sortedAsc[1].roster_id).toBe(2);

    // Pick WAR: Team Alpha (3.5) > Team Beta (1.0)
    const sortedPickDesc = sortRostersByStat(
      [mockRoster1, mockRoster2],
      'pick_rookie_war',
      'desc',
    );
    expect(sortedPickDesc[0].roster_id).toBe(1);
    expect(sortedPickDesc[1].roster_id).toBe(2);
  });

  it('computes summary statistics including user rank and value', () => {
    const sortedDesc = sortRostersByStat(
      [mockRoster1, mockRoster2],
      'dynasty_roster_war',
      'desc',
    );
    const summary = computeRosterStatSummary(
      mockLeague,
      sortedDesc,
      'dynasty_roster_war',
      'user-1',
    );

    expect(summary.max).toBe(15.0);
    expect(summary.min).toBe(12.4);
    expect(summary.avg).toBeCloseTo(13.7, 1);
    expect(summary.userRank).toBe(2);
    expect(summary.userValue).toBe(12.4);
  });
});
