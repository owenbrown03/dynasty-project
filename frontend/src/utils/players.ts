export function getSleeperPlayerHeadshotUrl(
  playerId: string | null | undefined,
): string | null {
  if (!playerId) {
    return null;
  }

  return `https://sleepercdn.com/content/nfl/players/thumb/${playerId}.jpg`;
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
