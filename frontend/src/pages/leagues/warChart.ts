import type { LeagueDetails } from '@/types';
import {
  CORE_FANTASY_POSITIONS,
  type FantasyPosition,
  getPositionColor,
} from '@/utils/positions';

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

export const WAR_CHART_POSITIONS = CORE_FANTASY_POSITIONS;

type WarMetricKey =
  (typeof WAR_CHART_METRICS)[number]['key'];

export interface LeaguePositionWarSeries {
  position: FantasyPosition;
  color: string;
  values: number[];
}

export function buildLeaguePositionWarSeries(
  league: LeagueDetails,
): LeaguePositionWarSeries[] {
  return WAR_CHART_POSITIONS.map((position) => ({
    position,
    color: getPositionColor(position),
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
  position: FantasyPosition,
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
