import { Fragment } from 'react';

import './PlayerTable.css';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type {
  LeaguePlayer,
  ValueBasis,
  WarValueSettings,
} from '@/types';
import { formatNumber } from '@/utils/format';
import { getPositionColor } from '@/utils/positions';
import {
  getLeaguePlayerSelectedValue,
  getValueBasisLabel,
} from '@/utils/valueBasis';

const FLEX_SLOT_POSITIONS: Record<string, string> = {
  FLEX: 'RB',
  WRRB_FLEX: 'RB',
  REC_FLEX: 'WR',
  WRTB_FLEX: 'WR',
  SUPER_FLEX: 'QB',
  IDP_FLEX: 'LB',
};

function normalizeSlotPosition(slot: string): string {
  return FLEX_SLOT_POSITIONS[slot] ?? slot;
}

function prettySlotLabel(slot: string | null | undefined): string {
  if (!slot) {
    return '-';
  }

  if (slot === 'WRRB_FLEX') return 'W/R';
  if (slot === 'REC_FLEX') return 'W/T';
  if (slot === 'WRTB_FLEX') return 'W/R/T';
  if (slot === 'SUPER_FLEX') return 'SF';
  if (slot === 'IDP_FLEX') return 'D';

  return slot;
}

interface Props {
  players: LeaguePlayer[];
  emptyStarterSlots?: string[] | null;
  valueBasis: ValueBasis;
  redraftValueBasis?: ValueBasis;
  warValueSettings: WarValueSettings;
}

export function PlayerTable({
  players,
  emptyStarterSlots,
  valueBasis,
  redraftValueBasis,
  warValueSettings,
}: Props) {
  const valueLabel = getValueBasisLabel(
    valueBasis,
  );
  const redraftLabel = redraftValueBasis
    ? getValueBasisLabel(redraftValueBasis)
    : null;

  const firstBenchIndex = players.findIndex(
    (player) => !player.is_starter,
  );

  return (
    <table className="player-table">
      <thead>
        <tr>
          <th>Slot</th>
          <th>Name</th>
          <th>Pos</th>
          <th>Team</th>
          <th>Proj</th>
          <th>UD</th>
          <th>{valueLabel}</th>
          {redraftLabel ? <th>{redraftLabel}</th> : null}
        </tr>
      </thead>

      <tbody>
        {players.map((player, index) => (
          <Fragment key={player.player_id}>
            {index === firstBenchIndex
              && firstBenchIndex > 0
              && (emptyStarterSlots ?? []).length > 0
              && (emptyStarterSlots ?? []).map((slot) => (
                <tr
                  key={`empty-${slot}`}
                  className="player-table-row-empty"
                >
                  <td className="player-table-slot-cell">
                    {prettySlotLabel(slot)}
                  </td>
                  <td colSpan={redraftLabel ? 7 : 6}>
                    Empty slot
                  </td>
                </tr>
              ))}
            {index === firstBenchIndex && firstBenchIndex > 0 && (
              <tr className="player-table-divider">
                <td colSpan={redraftLabel ? 8 : 7}>Bench</td>
              </tr>
            )}
            <tr
              className={
                player.is_starter
                  ? 'player-table-row-starter'
                  : undefined
              }
            >
              <td
                className="player-table-slot-cell"
                style={{
                  color: player.slot
                    ? getPositionColor(
                        normalizeSlotPosition(player.slot),
                      )
                    : undefined,
                }}
              >
                {prettySlotLabel(player.slot)}
              </td>
              <td className="player-table-name-cell">
                <div className="player-with-avatar">
                  <PlayerAvatar
                    playerId={player.player_id}
                    name={player.name}
                    size="sm"
                  />

                  <span className="player-table-name">
                    {player.name}
                  </span>
                </div>
              </td>
              <td
                className="player-table-position-cell"
                style={{
                  color: getPositionColor(player.position),
                }}
              >
                {player.position ?? '-'}
              </td>
              <td>{player.team ?? '-'}</td>
              <td>{formatNumber(player.projected_points)}</td>
              <td>{player.underdog_position_rank ?? '-'}</td>
              <td>
                {
                  formatNumber(
                    getLeaguePlayerSelectedValue(
                      player,
                      valueBasis,
                      warValueSettings,
                    ),
                    (
                      valueBasis === 'ktc'
                      || valueBasis === 'fantasycalc'
                      || valueBasis === 'adp'
                    )
                      ? 0
                      : 2,
                  )
                }
              </td>
              {redraftLabel ? (
                <td>
                  {
                    formatNumber(
                      getLeaguePlayerSelectedValue(
                        player,
                        redraftValueBasis as ValueBasis,
                        warValueSettings,
                      ),
                      (
                        redraftValueBasis === 'ktc'
                        || redraftValueBasis === 'fantasycalc'
                        || redraftValueBasis === 'adp'
                      )
                        ? 0
                        : 2,
                    )
                  }
                </td>
              ) : null}
            </tr>
          </Fragment>
        ))}
      </tbody>
    </table>
  );
}
