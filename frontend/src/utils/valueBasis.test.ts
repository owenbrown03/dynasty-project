import { describe, expect, it } from 'vitest';

import {
  getLeaguePlayerSelectedValue,
  getValueBasisLabel,
} from './valueBasis';
import { VALUE_BASIS_OPTIONS } from '@/pages/waivers/waiver.constants';
import type {
  LeaguePlayer,
  ValueBasis,
  WarValueSettings,
} from '@/types';

// Legacy bases that are no longer offered in the picker but remain
// valid stored preferences.
const LEGACY_BASES: ValueBasis[] = [
  'sleeper_war',
  'my_war',
  'redraft_roster_war',
  'redraft_starter_war',
];

const ALL_BASES: ValueBasis[] = [
  ...VALUE_BASIS_OPTIONS.map((option) => option.value),
  ...LEGACY_BASES,
];

const DEFAULT_WAR_SETTINGS: WarValueSettings = {
  sleeper_projection: { timeframe: 'dynasty', scope: 'roster' },
  my: { timeframe: 'dynasty', scope: 'roster' },
};

const PLAYER: LeaguePlayer = {
  player_id: '1',
  name: 'Test Player',
  position: 'RB',
  team: 'TST',
  age: 25,
  projected_points: 280.5,
  ktc_value: 5000,
  fc_value: 4800,
  adp_value: 120.5,
  redraft_starter_war: 4.2,
  redraft_roster_war: 6.1,
  dynasty_starter_war: 9.3,
  dynasty_roster_war: 14.7,
  my_redraft_starter_war: 4.0,
  my_redraft_roster_war: 5.9,
  my_dynasty_starter_war: 8.8,
  my_dynasty_roster_war: 13.9,
} as LeaguePlayer;

describe('value basis display coverage', () => {
  it('gives every basis a real label (no silent KTC fallback)', () => {
    for (const basis of ALL_BASES) {
      const label = getValueBasisLabel(basis);

      if (basis !== 'ktc') {
        expect(label, basis).not.toBe('KTC');
      }

      expect(label.length, basis).toBeGreaterThan(0);
    }
  });

  it('resolves a number for every basis on a populated player', () => {
    for (const basis of ALL_BASES) {
      const value = getLeaguePlayerSelectedValue(
        PLAYER,
        basis,
        DEFAULT_WAR_SETTINGS,
      );

      expect(value, basis).not.toBeNull();
      expect(value, basis).not.toBeNaN();
    }
  });
});
