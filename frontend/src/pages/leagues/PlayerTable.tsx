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
          <th className="player-table-slot-col">Slot</th>
          <th className="player-table-name-col">Name</th>
          <th className="player-table-pos-col">Pos</th>
          <th className="player-table-team-col">Team</th>
          <th className="player-table-num-col">Proj</th>
          <th className="player-table-ud-col">UD</th>
          <th className="player-table-num-col">{valueLabel}</th>
          {redraftLabel ? <th className="player-table-num-col">{redraftLabel}</th> : null}
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
                    <span className="player-table-slot-badge player-table-slot-badge-empty">
                      {prettySlotLabel(slot)}
                    </span>
                  </td>
                  <td colSpan={redraftLabel ? 7 : 6} className="player-table-empty-label">
                    Empty starter slot
                  </td>
                </tr>
              ))}
            {index === firstBenchIndex && firstBenchIndex > 0 && (
              <tr className="player-table-divider">
                <td colSpan={redraftLabel ? 8 : 7}>
                  <div className="player-table-divider-content">
                    <span className="player-table-divider-badge">Bench</span>
                  </div>
                </td>
              </tr>
            )}
            <tr
              className={
                player.is_starter
                  ? 'player-table-row-starter'
                  : 'player-table-row-bench'
              }
            >
              <td className="player-table-slot-cell">
                <span
                  className="player-table-slot-badge"
                  style={{
                    color: player.slot
                      ? getPositionColor(
                          normalizeSlotPosition(player.slot),
                        )
                      : undefined,
                    backgroundColor: player.slot
                      ? `color-mix(in srgb, ${getPositionColor(normalizeSlotPosition(player.slot))} 15%, transparent)`
                      : undefined,
                    borderColor: player.slot
                      ? `color-mix(in srgb, ${getPositionColor(normalizeSlotPosition(player.slot))} 35%, transparent)`
                      : undefined,
                  }}
                >
                  {prettySlotLabel(player.slot)}
                </span>
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
              <td className="player-table-team-cell">{player.team ?? '-'}</td>
              <td className="player-table-num-cell">{formatNumber(player.projected_points)}</td>
              <td className="player-table-ud-cell">{player.underdog_position_rank ?? '-'}</td>
              <td className="player-table-num-cell">
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
                <td className="player-table-num-cell">
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
