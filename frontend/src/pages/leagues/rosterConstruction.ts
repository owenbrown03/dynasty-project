import type { LeagueRoster } from '@/types';

const CORE_POSITIONS = [
  'QB',
  'RB',
  'WR',
  'TE',
] as const;

const FLEX_WEIGHTS: Record<
  string,
  Partial<Record<(typeof CORE_POSITIONS)[number], number>>
> = {
  FLEX: {
    RB: 0.4,
    WR: 0.4,
    TE: 0.2,
  },
  REC_FLEX: {
    RB: 0.35,
    WR: 0.45,
    TE: 0.2,
  },
  WRRB_FLEX: {
    RB: 0.5,
    WR: 0.5,
  },
  SUPER_FLEX: {
    QB: 0.55,
    RB: 0.15,
    WR: 0.2,
    TE: 0.1,
  },
  OP: {
    QB: 0.55,
    RB: 0.15,
    WR: 0.2,
    TE: 0.1,
  },
};

const WAR_ADJUSTMENT_WEIGHT = 0.35;

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
  rosterPositions: string[],
): RosterConstructionRow[] {
  const totalPlayers = Math.max(
    roster.players.length,
    1,
  );
  const starterDemandByPosition = buildStarterDemandByPosition(
    rosterPositions,
  );
  const totalStarterDemand = CORE_POSITIONS.reduce(
    (total, position) => (
      total + starterDemandByPosition[position]
    ),
    0,
  );
  const dynastyWarByPosition = buildDynastyWarByPosition(
    roster,
  );
  const totalDynastyWar = CORE_POSITIONS.reduce(
    (total, position) => (
      total + dynastyWarByPosition[position]
    ),
    0,
  );

  return CORE_POSITIONS.map((position) => {
    const playerCount = roster.players.filter(
      (player) => player.position === position,
    ).length;
    const baselineShare = totalStarterDemand > 0
      ? starterDemandByPosition[position] / totalStarterDemand
      : 1 / CORE_POSITIONS.length;
    const warShare = totalDynastyWar > 0
      ? dynastyWarByPosition[position] / totalDynastyWar
      : baselineShare;
    const targetCount = baselineShare * totalPlayers
      + (warShare - baselineShare) * totalPlayers * WAR_ADJUSTMENT_WEIGHT;

    return {
      position,
      playerCount,
      targetCount: roundCount(
        Math.max(
          starterDemandByPosition[position],
          targetCount,
        ),
      ),
      delta: roundCount(
        playerCount - Math.max(
          starterDemandByPosition[position],
          targetCount,
        ),
      ),
      warShare: roundPercent(
        warShare * 100,
      ),
    };
  });
}

function buildStarterDemandByPosition(
  rosterPositions: string[],
): Record<CorePosition, number> {
  const demand = {
    QB: 0,
    RB: 0,
    WR: 0,
    TE: 0,
  } satisfies Record<CorePosition, number>;

  for (const slot of rosterPositions) {
    if (slot in FLEX_WEIGHTS) {
      const weights = FLEX_WEIGHTS[slot];
      for (const position of CORE_POSITIONS) {
        demand[position] += weights[position] ?? 0;
      }
      continue;
    }

    if (
      CORE_POSITIONS.includes(
        slot as CorePosition,
      )
    ) {
      demand[slot as CorePosition] += 1;
    }
  }

  return demand;
}

function buildDynastyWarByPosition(
  roster: LeagueRoster,
): Record<CorePosition, number> {
  return roster.players.reduce(
    (totals, player) => {
      if (
        player.position
        && CORE_POSITIONS.includes(
          player.position as CorePosition,
        )
      ) {
        const position = player.position as CorePosition;
        totals[position] += Math.max(
          player.dynasty_roster_war ?? 0,
          0,
        );
      }

      return totals;
    },
    {
      QB: 0,
      RB: 0,
      WR: 0,
      TE: 0,
    } satisfies Record<CorePosition, number>,
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
