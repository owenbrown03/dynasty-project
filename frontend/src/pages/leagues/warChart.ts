import type { LeagueDetails } from '@/types';

export const WAR_CHART_METRICS = [
  {
    key: 'redraft_starter_war',
    label: 'Redraft starter',
  },
  {
    key: 'redraft_roster_war',
    label: 'Redraft roster',
  },
  {
    key: 'dynasty_starter_war',
    label: 'Dynasty starter',
  },
  {
    key: 'dynasty_roster_war',
    label: 'Dynasty roster',
  },
] as const;

export const WAR_CHART_POSITIONS = [
  'QB',
  'RB',
  'WR',
  'TE',
] as const;

type WarMetricKey =
  (typeof WAR_CHART_METRICS)[number]['key'];

export interface LeaguePositionWarSeries {
  position: (typeof WAR_CHART_POSITIONS)[number];
  color: string;
  values: number[];
}

const POSITION_COLORS: Record<
  (typeof WAR_CHART_POSITIONS)[number],
  string
> = {
  QB: '#1f6feb',
  RB: '#d97706',
  WR: '#059669',
  TE: '#c2410c',
};

export function buildLeaguePositionWarSeries(
  league: LeagueDetails,
): LeaguePositionWarSeries[] {
  return WAR_CHART_POSITIONS.map((position) => ({
    position,
    color: POSITION_COLORS[position],
    values: WAR_CHART_METRICS.map(({ key }) =>
      roundWar(
        sumPositionWar(
          league,
          position,
          key,
        ),
      ),
    ),
  }));
}

function sumPositionWar(
  league: LeagueDetails,
  position: (typeof WAR_CHART_POSITIONS)[number],
  key: WarMetricKey,
) {
  return league.rosters.reduce((total, roster) => (
    total + roster.players.reduce(
      (playerTotal, player) => (
        playerTotal + (
          player.position === position
            ? (player[key] ?? 0)
            : 0
        )
      ),
      0,
    )
  ), 0);
}

function roundWar(
  value: number,
) {
  return Math.round(value * 100) / 100;
}
