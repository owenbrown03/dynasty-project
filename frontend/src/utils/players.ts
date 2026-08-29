export function getSleeperPlayerHeadshotUrl(
  playerId: string | null | undefined,
): string | null {
  if (!playerId) {
    return null;
  }

  return `https://sleepercdn.com/content/nfl/players/thumb/${playerId}.jpg`;
}

const VALID_NFL_TEAMS = new Set([
  'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
  'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
  'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
  'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS',
]);

export function getSleeperTeamLogoUrl(
  team: string | null | undefined,
): string | null {
  if (!team) {
    return null;
  }

  const normalized = team.trim().toUpperCase();
  if (!VALID_NFL_TEAMS.has(normalized)) {
    return null;
  }

  return `https://sleepercdn.com/images/team_logos/nfl/${normalized.toLowerCase()}.png`;
}


export function getPlayerInitials(
  name: string | null | undefined,
): string {
  if (!name) {
    return '?';
  }

  const positionTokens = new Set([
    'QB',
    'RB',
    'WR',
    'TE',
    'K',
    'DEF',
    'DL',
    'DB',
    'LB',
  ]);

  const parts = name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .filter((part, index) => {
      if (index !== 0) {
        return true;
      }

      return !positionTokens.has(
        part.toUpperCase(),
      );
    });

  if (parts.length === 0) {
    return '?';
  }

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }

  return (
    `${parts[0][0] ?? ''}${parts[parts.length - 1][0] ?? ''}`
  ).toUpperCase();
}
