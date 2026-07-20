import type {
  LeagueRoster,
  LeagueRosterConstructionTarget,
} from '@/types';
import {
  CORE_FANTASY_POSITIONS,
  type FantasyPosition,
} from '@/utils/positions';

type CorePosition =
  FantasyPosition;

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

  return CORE_FANTASY_POSITIONS.map((position) => {
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
