import type { LeagueRoster } from '@/types';

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
): RosterConstructionRow[] {
  const totalPlayers = Math.max(
    roster.players.length,
    1,
  );
  const totalDynastyWar = CORE_POSITIONS.reduce(
    (total, position) => (
      total + getPositionWar(
        roster,
        position,
      )
    ),
    0,
  );

  return CORE_POSITIONS.map((position) => {
    const playerCount = roster.players.filter(
      (player) => player.position === position,
    ).length;
    const positionWar = getPositionWar(
      roster,
      position,
    );
    const warShare = totalDynastyWar > 0
      ? positionWar / totalDynastyWar
      : playerCount / totalPlayers;
    const targetCount = roundCount(
      warShare * totalPlayers,
    );

    return {
      position,
      playerCount,
      targetCount,
      delta: roundCount(
        playerCount - targetCount,
      ),
      warShare: roundPercent(
        warShare * 100,
      ),
    };
  });
}

function getPositionWar(
  roster: LeagueRoster,
  position: CorePosition,
) {
  return roster.players.reduce(
    (total, player) => (
      total + (
        player.position === position
          ? (player.dynasty_roster_war ?? 0)
          : 0
      )
    ),
    0,
  );
}

function roundCount(
  value: number,
) {
  return Math.round(value * 10) / 10;
}

function roundPercent(
  value: number,
) {
  return Math.round(value * 10) / 10;
}
