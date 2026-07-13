export type FantasyPosition =
  | 'QB'
  | 'RB'
  | 'WR'
  | 'TE';

const POSITION_COLOR_BY_KEY = {
  QB: 'var(--position-qb-color)',
  RB: 'var(--position-rb-color)',
  WR: 'var(--position-wr-color)',
  TE: 'var(--position-te-color)',
} as const;

export function getPositionColor(
  position: string | null | undefined,
) {
  if (
    position === 'QB'
    || position === 'RB'
    || position === 'WR'
    || position === 'TE'
  ) {
    return POSITION_COLOR_BY_KEY[position];
  }

  return 'var(--color-border-strong)';
}


export function getDraftPickColor() {
  return 'var(--position-pick-color)';
}
