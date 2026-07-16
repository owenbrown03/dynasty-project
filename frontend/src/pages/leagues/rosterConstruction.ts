import type {
  LeagueRoster,
  LeagueRosterConstructionTarget,
} from '@/types';

const CORE_POSITIONS = [
  'QB',
  'RB',
  'WR',
  'TE',
] as const;

type CorePosition =
  (typeof CORE_POSITIONS)[number];

export interface RosterConstructionRow {
  position: CorePosition;
  playerCount: number;
  targetCount: number;
  delta: number;
  warShare: number;
}

export function buildRosterConstructionRows(
  roster: LeagueRoster,
  targets: LeagueRosterConstructionTarget[],
): RosterConstructionRow[] {
  const targetsByPosition = new Map(
    targets.map(
      target => [
        target.position,
        target,
      ],
    ),
  );

  return CORE_POSITIONS.map((position) => {
    const playerCount = roster.players.filter(
      player => player.position === position,
    ).length;
    const target = targetsByPosition.get(position);

    return {
      position,
      playerCount,
      targetCount: target?.target_count ?? 0,
      delta: playerCount - (target?.target_count ?? 0),
      warShare: roundPercent(
        target?.war_share ?? 0,
      ),
    };
  });
}

function roundPercent(
  value: number,
) {
  return Math.round(value * 10) / 10;
}
