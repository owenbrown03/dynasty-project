import { describe, expect, it } from 'vitest';

import type { FinanceLeagueSeasonEntry } from '@/types';

import {
  addPayoutRow,
  buildCurrentFinanceTimeline,
  buildPayoutRows,
  buildSeasonChartEntries,
  draftRowsEqual,
  effectiveFinanceNet,
  effectiveFinanceWinnings,
  financeResultLabel,
  ordinal,
} from './finance.utils';

function financeEntry(
  overrides: Partial<FinanceLeagueSeasonEntry> = {},
): FinanceLeagueSeasonEntry {
  return {
    league_id: 'league-1',
    league_family_id: 'family-1',
    league_name: 'Test League',
    season: '2026',
    status: 'in_season',
    total_rosters: 12,
    rank: null,
    wins: null,
    losses: null,
    points_for: null,
    finish_place: null,
    projected_finish_place: null,
    buy_in_amount: 25,
    winnings_amount: 0,
    payout_structure: [],
    buy_in_source: 'global_default',
    payout_source: 'global_default',
    has_season_override: false,
    has_league_default: false,
    is_excluded: false,
    projected_winnings_amount: 40,
    projected_winnings_source: 'seed_probability',
    net_amount: -25,
    ...overrides,
  };
}

describe('finance utils', () => {
  it('formats ordinal labels', () => {
    expect(ordinal(1)).toBe('1st');
    expect(ordinal(2)).toBe('2nd');
    expect(ordinal(3)).toBe('3rd');
    expect(ordinal(4)).toBe('4th');
    expect(ordinal(11)).toBe('11th');
    expect(ordinal(12)).toBe('12th');
    expect(ordinal(13)).toBe('13th');
    expect(ordinal(21)).toBe('21st');
  });

  it('builds editable payout rows', () => {
    expect(buildPayoutRows([])).toEqual([
      {
        place: '1',
        amount: '',
      },
    ]);

    expect(
      addPayoutRow({
        buyInAmount: '25',
        payoutStructure: [
          {
            place: '1',
            amount: '200',
          },
          {
            place: '3',
            amount: '25',
          },
        ],
      }).payoutStructure.at(-1),
    ).toEqual({
      place: '4',
      amount: '',
    });
  });

  it('compares normalized payout rows', () => {
    expect(
      draftRowsEqual(
        [
          {
            place: '2',
            amount: '75',
          },
          {
            place: '1',
            amount: '200',
          },
          {
            place: '0',
            amount: '999',
          },
        ],
        [
          {
            place: '1',
            amount: '200.00',
          },
          {
            place: '2',
            amount: '75',
          },
        ],
      ),
    ).toBe(true);

    expect(
      draftRowsEqual(
        [
          {
            place: '1',
            amount: '200',
          },
        ],
        [
          {
            place: '1',
            amount: '250',
          },
        ],
      ),
    ).toBe(false);
  });

  it('labels finance results from actual finish, projection, rank, or team count', () => {
    expect(
      financeResultLabel(
        financeEntry({
          finish_place: 2,
          projected_finish_place: 5,
          rank: 8,
        }),
      ),
    ).toBe('Finish 2nd of 12');

    expect(
      financeResultLabel(
        financeEntry({
          projected_finish_place: 5,
          rank: 8,
        }),
      ),
    ).toBe('Projected seed 5th of 12');

    expect(
      financeResultLabel(
        financeEntry({
          rank: 8,
        }),
      ),
    ).toBe('Current rank 8th of 12');

    expect(financeResultLabel(financeEntry())).toBe('12 teams');
  });

  it('uses actual winnings only for complete seasons', () => {
    const active = financeEntry({
      status: 'in_season',
      buy_in_amount: 25,
      winnings_amount: 200,
      projected_winnings_amount: 40,
    });

    expect(effectiveFinanceWinnings(active)).toBe(40);
    expect(effectiveFinanceNet(active)).toBe(15);

    const complete = financeEntry({
      status: 'complete',
      buy_in_amount: 25,
      winnings_amount: 200,
      projected_winnings_amount: 40,
    });

    expect(effectiveFinanceWinnings(complete)).toBe(200);
    expect(effectiveFinanceNet(complete)).toBe(175);
  });

  it('builds season chart entries with projected current seasons', () => {
    const entries = buildSeasonChartEntries([
      financeEntry({
        league_id: '2025-a',
        season: '2025',
        status: 'complete',
        buy_in_amount: 25,
        winnings_amount: 200,
        projected_winnings_amount: 0,
      }),
      financeEntry({
        league_id: '2026-a',
        season: '2026',
        status: 'in_season',
        buy_in_amount: 25,
        winnings_amount: 200,
        projected_winnings_amount: 40,
      }),
    ]);

    expect(entries).toMatchObject([
      {
        label: '2025',
        subLabel: '1 league',
        winningsAmount: 200,
        netAmount: 175,
        isProjected: false,
      },
      {
        label: '2026',
        subLabel: '1 league · projected',
        winningsAmount: 40,
        netAmount: 15,
        isProjected: true,
      },
    ]);
  });

  it('builds the current finance timeline point', () => {
    expect(buildCurrentFinanceTimeline([])).toEqual([]);

    expect(
      buildCurrentFinanceTimeline([
        financeEntry({
          status: 'in_season',
          projected_winnings_amount: 40,
          winnings_amount: 200,
        }),
        financeEntry({
          league_id: 'league-2',
          status: 'complete',
          projected_winnings_amount: 60,
          winnings_amount: 200,
        }),
      ]),
    ).toEqual([
      {
        week: 1,
        label: 'Week 1',
        actualAmount: 240,
        projectedAmount: 100,
      },
    ]);
  });
});
