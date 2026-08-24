import { describe, expect, it } from 'vitest';

import {
  isLeagueContextValueBasis,
  LEAGUE_CONTEXT_VALUE_BASES,
  TIER_SOURCE_OPTIONS,
} from './tier.constants';
import { VALUE_BASIS_OPTIONS } from '@/pages/waivers/waiver.constants';

describe('tier board source lists', () => {
  it('offers the settings pool plus the redraft value sources', () => {
    // Selector-surface principle: the settings pool, extended with
    // the redraft value sources (#165).
    const poolValues = VALUE_BASIS_OPTIONS.map((o) => o.value);

    for (const option of VALUE_BASIS_OPTIONS) {
      expect(
        TIER_SOURCE_OPTIONS.some((o) => o.value === option.value),
      ).toBe(true);
    }

    expect(
      TIER_SOURCE_OPTIONS.some((o) => o.value === 'redraft_roster_war'),
    ).toBe(true);
    expect(
      TIER_SOURCE_OPTIONS.some((o) => o.value === 'redraft_starter_war'),
    ).toBe(true);
    expect(poolValues).not.toContain('redraft_roster_war');
  });

  it('flags the league-context bases for league selection', () => {
    const standalone = TIER_SOURCE_OPTIONS.filter(
      (option) => !isLeagueContextValueBasis(option.value),
    ).map((option) => option.value);

    for (const basis of LEAGUE_CONTEXT_VALUE_BASES) {
      expect(standalone).not.toContain(basis);
      expect(isLeagueContextValueBasis(basis)).toBe(true);
    }
  });

  it('classifies the bases that crashed the board as league-context', () => {
    expect(isLeagueContextValueBasis('my_roster_war')).toBe(true);
    expect(isLeagueContextValueBasis('my_starter_war')).toBe(true);
    expect(isLeagueContextValueBasis('dynasty_roster_war')).toBe(true);
    expect(isLeagueContextValueBasis('sleeper_projection')).toBe(true);
    expect(isLeagueContextValueBasis('ktc')).toBe(false);
  });
});
