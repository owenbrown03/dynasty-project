import { describe, expect, it } from 'vitest';

import type {
  PersonalValueMetrics,
  PersonalValuePlayer,
  PersonalValuePoolItem,
} from '@/types';

import {
  cloneSeasons,
  comparePoolItems,
  formatMarketNumber,
  formatMetric,
  buildNextTableFilter,
  getDefaultFutureOutcomes,
  getDefaultSortColumn,
  getFallbackOutcomes,
  getPoolPlayerIds,
  itemMatchesFilter,
  parseUnderdogRank,
} from './myValues.utils';

function poolItem(
  overrides: Partial<Omit<PersonalValuePoolItem, 'player' | 'market_values' | 'custom_values' | 'delta_values'>> & {
    player?: Partial<PersonalValuePlayer>;
    market_values?: Partial<PersonalValueMetrics>;
    custom_values?: Partial<PersonalValueMetrics>;
    delta_values?: Partial<PersonalValueMetrics>;
  } = {},
): PersonalValuePoolItem {
  const base: PersonalValuePoolItem = {
    player: {
      player_id: 'player-1',
      name: 'Josh Downs',
      position: 'WR',
      team: 'IND',
      age: 24,
      underdog_position_rank: 'WR48',
      ktc_value: 4200,
      fc_value: 3900,
      adp_value: 96,
    },
    market_values: {
      redraft_starter_war: 1,
      redraft_roster_war: 2,
      dynasty_starter_war: 3,
      dynasty_roster_war: 4,
    },
    custom_values: {
      redraft_starter_war: 1.5,
      redraft_roster_war: 2.5,
      dynasty_starter_war: 3.5,
      dynasty_roster_war: 4.5,
    },
    delta_values: {
      redraft_starter_war: 0.5,
      redraft_roster_war: 0.5,
      dynasty_starter_war: 0.5,
      dynasty_roster_war: 0.5,
    },
    is_customized: false,
  };

  return {
    ...base,
    ...overrides,
    player: {
      ...base.player,
      ...overrides.player,
    },
    market_values: {
      ...base.market_values,
      ...overrides.market_values,
    },
    custom_values: {
      ...base.custom_values,
      ...overrides.custom_values,
    },
    delta_values: {
      ...base.delta_values,
      ...overrides.delta_values,
    },
  };
}

describe('myValues utils', () => {
  it('chooses the default sort column from the selected value basis', () => {
    expect(getDefaultSortColumn('fantasycalc')).toBe('fantasycalc');
    expect(getDefaultSortColumn('adp')).toBe('adp');
    expect(getDefaultSortColumn('ktc')).toBe('ktc');
    expect(getDefaultSortColumn('my_war')).toBe('my_war');
    expect(getDefaultSortColumn('dynasty_roster_war')).toBe('my_war');
  });

  it('formats market and WAR values', () => {
    expect(formatMetric(null)).toBe('--');
    expect(formatMetric(1.234)).toBe('1.23');
    expect(formatMarketNumber(undefined)).toBe('--');
    expect(formatMarketNumber(1234.4)).toBe('1,234');
  });

  it('parses underdog ranks conservatively', () => {
    expect(parseUnderdogRank('WR48')).toBe(48);
    expect(parseUnderdogRank('QB 12')).toBe(12);
    expect(parseUnderdogRank(null)).toBe(Number.POSITIVE_INFINITY);
    expect(parseUnderdogRank('UD')).toBe(Number.POSITIVE_INFINITY);
  });

  it('sorts by position first, then selected column', () => {
    const qb = poolItem({
      player: {
        player_id: 'qb',
        name: 'Drake Maye',
        position: 'QB',
        ktc_value: 1000,
      },
    });
    const wr = poolItem({
      player: {
        player_id: 'wr',
        name: 'JaMarr Chase',
        position: 'WR',
        ktc_value: 10000,
      },
    });

    expect(
      [wr, qb].sort((left, right) => (
        comparePoolItems(
          left,
          right,
          'ktc',
          'desc',
        )
      )),
    ).toEqual([qb, wr]);
  });

  it('applies table filters across string and numeric columns', () => {
    const item = poolItem();

    expect(
      itemMatchesFilter(
        item,
        {
          id: 1,
          column: 'player',
          operator: 'contains',
          value: 'downs',
        },
      ),
    ).toBe(true);
    expect(
      itemMatchesFilter(
        item,
        {
          id: 2,
          column: 'team',
          operator: 'equals',
          value: 'ind',
        },
      ),
    ).toBe(true);
    expect(
      itemMatchesFilter(
        item,
        {
          id: 3,
          column: 'my_war',
          operator: 'gt',
          value: '4',
        },
      ),
    ).toBe(true);
    expect(
      itemMatchesFilter(
        item,
        {
          id: 4,
          column: 'ktc',
          operator: 'lt',
          value: '4000',
        },
      ),
    ).toBe(false);
  });

  it('builds the next table filter with a deterministic id', () => {
    expect(
      buildNextTableFilter([
        {
          id: 1,
          column: 'player',
          operator: 'contains',
          value: 'downs',
        },
        {
          id: 7,
          column: 'team',
          operator: 'equals',
          value: 'IND',
        },
      ]),
    ).toEqual({
      id: 8,
      column: 'player',
      operator: 'contains',
      value: '',
    });
  });

  it('clones seasons and fills the current empty season from default rank', () => {
    const seasons = [
      {
        season: 2026,
        outcomes: [],
        default_position_rank: 48,
        is_customized: false,
      },
      {
        season: 2027,
        outcomes: [
          {
            position_rank: 60,
            probability: 100,
          },
        ],
        default_position_rank: 55,
        is_customized: false,
      },
    ];

    const cloned = cloneSeasons(seasons);
    expect(cloned).toEqual([
      {
        season: 2026,
        outcomes: [
          {
            position_rank: 48,
            probability: 100,
          },
        ],
        default_position_rank: 48,
        is_customized: false,
      },
      seasons[1],
    ]);
    expect(cloned).not.toBe(seasons);
    expect(cloned[1].outcomes).not.toBe(seasons[1].outcomes);
  });

  it('builds fallback and default future outcomes', () => {
    expect(
      getFallbackOutcomes({
        season: 2027,
        outcomes: [],
        default_position_rank: 70,
        is_customized: false,
      }),
    ).toEqual([
      {
        position_rank: 70,
        probability: 100,
      },
    ]);

    expect(
      getDefaultFutureOutcomes(
        [
          {
            season: 2026,
            outcomes: [
              {
                position_rank: 48,
                probability: 100,
              },
            ],
            default_position_rank: 48,
            is_customized: true,
          },
          {
            season: 2027,
            outcomes: [],
            default_position_rank: 60,
            is_customized: false,
          },
        ],
        2026,
      ),
    ).toEqual([
      {
        position_rank: 60,
        probability: 100,
      },
    ]);
  });

  it('returns unique pool player ids', () => {
    expect(
      getPoolPlayerIds([
        poolItem({
          player: {
            player_id: 'a',
          },
        }),
        poolItem({
          player: {
            player_id: 'b',
          },
        }),
      ]),
    ).toEqual(new Set(['a', 'b']));
  });
});
