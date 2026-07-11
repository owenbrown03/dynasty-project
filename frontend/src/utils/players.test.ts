import { describe, expect, it } from 'vitest';

import {
  getPlayerInitials,
  getSleeperPlayerHeadshotUrl,
} from './players';


describe('players utils', () => {
  it('builds sleeper headshot urls', () => {
    expect(
      getSleeperPlayerHeadshotUrl('1234'),
    ).toBe(
      'https://sleepercdn.com/content/nfl/players/thumb/1234.jpg',
    );
  });

  it('returns null when no player id is provided', () => {
    expect(
      getSleeperPlayerHeadshotUrl(null),
    ).toBeNull();
  });

  it('omits leading position tokens when deriving initials', () => {
    expect(
      getPlayerInitials('QB Josh Allen'),
    ).toBe('JA');
  });

  it('handles single-token names', () => {
    expect(
      getPlayerInitials('Madonna'),
    ).toBe('MA');
  });
});
