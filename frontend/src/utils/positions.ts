export const CORE_FANTASY_POSITIONS = [
  'QB',
  'RB',
  'WR',
  'TE',
] as const;

export type FantasyPosition =
  (typeof CORE_FANTASY_POSITIONS)[number];

const POSITION_COLOR_BY_KEY = {
  QB: 'var(--position-qb-color)',
  RB: 'var(--position-rb-color)',
  WR: 'var(--position-wr-color)',
  TE: 'var(--position-te-color)',
} as const;

export function getPositionColor(
  position: string | null | undefined,
) {
  if (isCoreFantasyPosition(position)) {
    return POSITION_COLOR_BY_KEY[position];
  }

  return 'var(--color-border-strong)';
}


export function isCoreFantasyPosition(
  position: string | null | undefined,
): position is FantasyPosition {
  return CORE_FANTASY_POSITIONS.includes(
    position as FantasyPosition,
  );
}


export function getDraftPickColor() {
  return 'var(--position-pick-color)';
}
