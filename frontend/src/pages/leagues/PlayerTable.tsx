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

function getCompactValueBasisMeta(valueBasis: ValueBasis): { label: string; tooltip: string } {
  switch (valueBasis) {
    case 'dynasty_roster_war':
      return { label: 'D-WAR', tooltip: 'Dynasty Roster WAR' };
    case 'dynasty_starter_war':
      return { label: 'D-WAR', tooltip: 'Dynasty Starter WAR' };
    case 'my_roster_war':
      return { label: 'D-WAR', tooltip: 'Dynasty Roster WAR (My Model)' };
    case 'my_starter_war':
      return { label: 'D-WAR', tooltip: 'Dynasty Starter WAR (My Model)' };
    case 'redraft_roster_war':
      return { label: 'R-WAR', tooltip: 'Redraft Roster WAR' };
    case 'redraft_starter_war':
      return { label: 'R-WAR', tooltip: 'Redraft Starter WAR' };
    case 'sleeper_war':
      return { label: 'S-WAR', tooltip: 'Sleeper WAR' };
    case 'my_war':
      return { label: 'My WAR', tooltip: 'My Custom WAR' };
    case 'fantasycalc':
      return { label: 'FC', tooltip: 'FantasyCalc Dynasty Value' };
    case 'fantasycalc_redraft':
      return { label: 'FC (R)', tooltip: 'FantasyCalc Redraft Value' };
    case 'ktc':
      return { label: 'KTC', tooltip: 'KeepTradeCut Dynasty Value' };
    case 'ktc_redraft':
      return { label: 'KTC (R)', tooltip: 'KeepTradeCut Redraft Value' };
    case 'adp':
      return { label: 'ADP', tooltip: 'Average Draft Position' };
    case 'sleeper_projection':
      return { label: 'Proj', tooltip: 'Sleeper Projected Points' };
    default:
      return {
        label: getValueBasisLabel(valueBasis),
        tooltip: getValueBasisLabel(valueBasis),
      };
  }
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
  const valueMeta = getCompactValueBasisMeta(valueBasis);
  const redraftMeta = redraftValueBasis
    ? getCompactValueBasisMeta(redraftValueBasis)
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
          <th className="player-table-num-col" title="Projected Points">Proj</th>
          <th className="player-table-ud-col" title="Underdog Position Rank">UD</th>
          <th className="player-table-num-col" title={valueMeta.tooltip}>{valueMeta.label}</th>
          {redraftMeta ? (
            <th className="player-table-num-col" title={redraftMeta.tooltip}>
              {redraftMeta.label}
            </th>
          ) : null}
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
                    <span className="player-table-slot-text player-table-slot-text-empty">
                      {prettySlotLabel(slot)}
                    </span>
                  </td>
                  <td colSpan={redraftMeta ? 7 : 6} className="player-table-empty-label">
                    Empty starter slot
                  </td>
                </tr>
              ))}
            {index === firstBenchIndex && firstBenchIndex > 0 && (
              <tr className="player-table-divider">
                <td colSpan={redraftMeta ? 8 : 7}>
                  <div className="player-table-divider-inner">
                    <span>Bench</span>
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
                  className="player-table-slot-text"
                  style={{
                    color: player.slot
                      ? getPositionColor(
                          normalizeSlotPosition(player.slot),
                        )
                      : 'var(--color-text-muted)',
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
