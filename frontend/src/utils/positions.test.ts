import { describe, expect, it } from 'vitest';

import {
  CORE_FANTASY_POSITION_ORDER,
  CORE_FANTASY_POSITIONS,
  getPositionColor,
  isCoreFantasyPosition,
} from './positions';

describe('position utilities', () => {
  it('keeps core fantasy positions in the shared display order', () => {
    expect(CORE_FANTASY_POSITIONS).toEqual([
      'QB',
      'RB',
      'WR',
      'TE',
    ]);
    expect(CORE_FANTASY_POSITION_ORDER.QB).toBe(0);
    expect(CORE_FANTASY_POSITION_ORDER.RB).toBe(1);
    expect(CORE_FANTASY_POSITION_ORDER.WR).toBe(2);
    expect(CORE_FANTASY_POSITION_ORDER.TE).toBe(3);
  });

  it('identifies and colors core positions only', () => {
    expect(isCoreFantasyPosition('WR')).toBe(true);
    expect(isCoreFantasyPosition('K')).toBe(false);
    expect(getPositionColor('WR')).toBe('var(--position-wr-color)');
    expect(getPositionColor('K')).toBe('var(--color-border-strong)');
  });
});
