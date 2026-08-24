import type {
  LeagueRoster,
  LeagueRosterConstructionTarget,
  ValueBasis,
  WarValueSettings,
} from '@/types';
import {
  CORE_FANTASY_POSITIONS,
  type FantasyPosition,
} from '@/utils/positions';
import { getLeaguePlayerSelectedValue } from '@/utils/valueBasis';

type CorePosition =
  FantasyPosition;

export interface RosterConstructionRow {
  position: CorePosition;
  playerCount: number;
  targetCount: number;
  delta: number;
  warShare: number;
  projectedPoints: number;
  selectedValue: number;
  redraftValue: number;
}

export function buildRosterConstructionRows(
  roster: LeagueRoster,
  targets: LeagueRosterConstructionTarget[],
  valueSettings?: {
    valueBasis: ValueBasis;
    redraftValueBasis?: ValueBasis;
    warValueSettings: WarValueSettings;
  },
): RosterConstructionRow[] {
  const targetsByPosition = new Map(
    targets.map(
      target => [
        target.position,
        target,
      ],
    ),
  );

  const redraftValueBasis = valueSettings?.redraftValueBasis;

  return CORE_FANTASY_POSITIONS.map((position) => {
    const positionPlayers = roster.players.filter(
      player => player.position === position,
    );
    const target = targetsByPosition.get(position);

    return {
      position,
      playerCount: positionPlayers.length,
      targetCount: target?.target_count ?? 0,
      delta: positionPlayers.length - (target?.target_count ?? 0),
      warShare: roundPercent(
        target?.war_share ?? 0,
      ),
      projectedPoints: roundPercent(
        sumValues(
          positionPlayers.map(
            player => player.projected_points,
          ),
        ),
      ),
      redraftValue: redraftValueBasis
        ? roundPercent(
            sumValues(
              positionPlayers.map(
                player =>
                  getLeaguePlayerSelectedValue(
                    player,
                    redraftValueBasis,
                    valueSettings?.warValueSettings ??
                    { sleeper_projection: { timeframe: 'dynasty', scope: 'roster' }, my: { timeframe: 'dynasty', scope: 'roster' } },
                  ),
              ),
            ),
          )
        : 0,
      selectedValue: valueSettings
        ? roundPercent(
            sumValues(
              positionPlayers.map(
                player =>
                  getLeaguePlayerSelectedValue(
                    player,
                    valueSettings.valueBasis,
                    valueSettings.warValueSettings,
                  ),
              ),
            ),
          )
        : 0,
    };
  });
}

function sumValues(
  values: Array<number | null | undefined>,
): number {
  return values.reduce<number>(
    (total, value) => total + (value ?? 0),
    0,
  );
}

function roundPercent(
  value: number,
) {
  return Math.round(value * 10) / 10;
}
