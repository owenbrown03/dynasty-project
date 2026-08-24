import { describe, expect, it } from 'vitest';

import {
  isLeagueContextValueBasis,
  LEAGUE_CONTEXT_VALUE_BASES,
  TIER_SOURCE_OPTIONS,
  WAR_ONLY_OPTIONS,
} from './tier.constants';
import { VALUE_BASIS_OPTIONS } from '@/pages/waivers/waiver.constants';

describe('tier board source lists', () => {
  it('keeps the source lists in sync with the league-context set', () => {
    const standaloneSources = TIER_SOURCE_OPTIONS.map(
      (option) => option.value,
    );
    const warSources = WAR_ONLY_OPTIONS.map(
      (option) => option.value,
    );

    for (const basis of LEAGUE_CONTEXT_VALUE_BASES) {
      expect(standaloneSources).not.toContain(basis);
      expect(warSources).toContain(basis);
    }
  });

  it('derives every source option from the value pool or League WAR', () => {
    const poolValues = VALUE_BASIS_OPTIONS.map(
      (option) => option.value,
    );

    for (const option of TIER_SOURCE_OPTIONS) {
      if (option.value === 'league_war') {
        continue;
      }

      expect(poolValues).toContain(option.value);
    }
  });

  it('classifies the bases that crashed the board as league-context', () => {
    expect(
      isLeagueContextValueBasis('my_roster_war'),
    ).toBe(true);
    expect(
      isLeagueContextValueBasis('my_starter_war'),
    ).toBe(true);
    expect(
      isLeagueContextValueBasis('dynasty_roster_war'),
    ).toBe(true);
    expect(
      isLeagueContextValueBasis('sleeper_projection'),
    ).toBe(true);
    expect(isLeagueContextValueBasis('ktc')).toBe(false);
  });
});
