import { describe, expect, it } from 'vitest';

import {
  getPlayerInitials,
  getSleeperPlayerHeadshotUrl,
  getSleeperTeamLogoUrl,
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

  it('builds sleeper team logo urls for valid NFL teams', () => {
    expect(getSleeperTeamLogoUrl('BAL')).toBe(
      'https://sleepercdn.com/images/team_logos/nfl/bal.png',
    );
    expect(getSleeperTeamLogoUrl('kc')).toBe(
      'https://sleepercdn.com/images/team_logos/nfl/kc.png',
    );
  });

  it('returns null for non-NFL team or FA', () => {
    expect(getSleeperTeamLogoUrl('FA')).toBeNull();
    expect(getSleeperTeamLogoUrl(null)).toBeNull();
    expect(getSleeperTeamLogoUrl('UNKNOWN')).toBeNull();
  });
});
