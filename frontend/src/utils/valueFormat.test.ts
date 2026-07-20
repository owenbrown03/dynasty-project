import { describe, expect, it } from 'vitest';

import {
  formatAge,
  formatDollarAmount,
  formatMarketValue,
  formatSelectedValue,
  formatWar,
  isMarketValueBasis,
} from './valueFormat';

describe('valueFormat', () => {
  it('identifies market value bases', () => {
    expect(isMarketValueBasis('ktc')).toBe(true);
    expect(isMarketValueBasis('fantasycalc')).toBe(true);
    expect(isMarketValueBasis('adp')).toBe(true);
    expect(isMarketValueBasis('my_war')).toBe(false);
  });

  it('formats selected values consistently by basis', () => {
    expect(formatSelectedValue(null, 'ktc')).toBe('—');
    expect(formatSelectedValue(1234.6, 'ktc')).toBe('1,235');
    expect(formatSelectedValue(1.23456, 'my_war')).toBe('1.235');
    expect(formatSelectedValue(-0.4101, 'dynasty_roster_war')).toBe('-0.410');
  });

  it('formats common value primitives', () => {
    expect(formatAge(null)).toBe('—');
    expect(formatAge(24.36)).toBe('24.4');
    expect(formatMarketValue(undefined)).toBe('—');
    expect(formatMarketValue(9876.4)).toBe('9,876');
    expect(formatWar(null)).toBe('—');
    expect(formatWar(1.23456)).toBe('1.235');
    expect(formatDollarAmount(undefined)).toBe('--');
    expect(formatDollarAmount(1234.5)).toBe('$1,235');
  });
});
