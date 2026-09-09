import { describe, expect, it } from 'vitest';
import { getValidSleeperPickYears } from './picks';

describe('getValidSleeperPickYears', () => {
  it('returns current year and the next 3 future seasons', () => {
    const fixedDate = new Date(2026, 8, 9);
    const years = getValidSleeperPickYears(fixedDate);
    expect(years).toEqual(['2026', '2027', '2028', '2029']);
  });
});
