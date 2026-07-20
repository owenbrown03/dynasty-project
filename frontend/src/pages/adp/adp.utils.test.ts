import { describe, expect, it } from 'vitest';

import {
  buildBoardDisplayRows,
  buildBoardRounds,
  buildDynamicOptions,
  compareRows,
  getDefaultDraftOrderMode,
  getDisplaySlotForColumn,
  readDraftOrderModeParam,
  readFiltersFromSearchParams,
} from './adp.utils';
import type { ADPPlayerRow } from '@/types';

function player(
  id: string,
  name: string,
  position: string,
  overallAdp: number,
): ADPPlayerRow {
  return {
    player_id: id,
    name,
    position,
    team: 'FA',
    overall_adp: overallAdp,
    median_pick: overallAdp,
    min_pick: Math.floor(overallAdp),
    max_pick: Math.ceil(overallAdp),
    standard_deviation: null,
    pick_count: 10,
    draft_count: 10,
    selection_rate: 1,
  };
}

describe('ADP utilities', () => {
  it('defaults rookie drafts to linear and startups to snake', () => {
    expect(getDefaultDraftOrderMode('rookie')).toBe('linear');
    expect(getDefaultDraftOrderMode('startup')).toBe('snake');
    expect(readDraftOrderModeParam('bad-value', 'rookie')).toBe('linear');
    expect(readDraftOrderModeParam('third_round_reversal', 'startup')).toBe(
      'third_round_reversal',
    );
  });

  it('maps board slots for snake, linear, and 3RR layouts', () => {
    expect(getDisplaySlotForColumn(2, 0, 4, 'linear')).toBe(1);
    expect(getDisplaySlotForColumn(2, 0, 4, 'snake')).toBe(4);
    expect(getDisplaySlotForColumn(3, 0, 4, 'snake')).toBe(1);
    expect(getDisplaySlotForColumn(3, 0, 4, 'third_round_reversal')).toBe(4);
    expect(getDisplaySlotForColumn(4, 0, 4, 'third_round_reversal')).toBe(1);
  });

  it('builds board rows with position ranks and snake display order', () => {
    const rounds = buildBoardRounds(
      [
        player('1', 'Alpha QB', 'QB', 1),
        player('2', 'Beta RB', 'RB', 2),
        player('3', 'Gamma QB', 'QB', 3),
        player('4', 'Delta WR', 'WR', 4),
      ],
      2,
    );

    expect(rounds[0].players.map((entry) => entry.positionRankLabel)).toEqual([
      'QB1',
      'RB1',
    ]);
    expect(rounds[1].players.map((entry) => entry.positionRankLabel)).toEqual([
      'QB2',
      'WR1',
    ]);

    const displayRows = buildBoardDisplayRows(rounds, 2, 'snake');
    expect(displayRows[0].cells.map((cell) => cell.entry?.player.name)).toEqual([
      'Alpha QB',
      'Beta RB',
    ]);
    expect(displayRows[1].cells.map((cell) => cell.entry?.player.name)).toEqual([
      'Delta WR',
      'Gamma QB',
    ]);
  });

  it('parses filter search params with numeric fallbacks', () => {
    const filters = readFiltersFromSearchParams(
      new URLSearchParams(
        'season=2026&draft_kind=rookie&team_count=abc&limit=500',
      ),
    );

    expect(filters.season).toBe('2026');
    expect(filters.draft_kind).toBe('rookie');
    expect(filters.team_count).toBe(12);
    expect(filters.limit).toBe(500);
  });

  it('builds dynamic options and skips unknown rows', () => {
    expect(
      buildDynamicOptions(
        [
          { key: 'superflex', count: 3 },
          { key: 'unknown', count: 9 },
        ],
        {
          allLabel: 'All formats',
          labelMap: { superflex: 'Superflex' },
        },
      ),
    ).toEqual([
      { value: '', label: 'All formats' },
      { value: 'superflex', label: 'Superflex (3)' },
    ]);
  });

  it('sorts numeric and text columns consistently', () => {
    const alpha = player('1', 'Alpha', 'QB', 10);
    const beta = player('2', 'Beta', 'RB', 5);

    expect(compareRows(alpha, beta, 'overall_adp', 'asc')).toBeGreaterThan(0);
    expect(compareRows(alpha, beta, 'overall_adp', 'desc')).toBeLessThan(0);
    expect(compareRows(alpha, beta, 'name', 'asc')).toBeLessThan(0);
  });
});
