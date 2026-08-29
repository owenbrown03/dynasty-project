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

interface SlotSegment {
  letter: string;
  position?: string;
}

function getSlotSegments(slot: string | null | undefined): SlotSegment[] {
  if (!slot) {
    return [{ letter: '-' }];
  }

  switch (slot) {
    case 'FLEX':
    case 'WRTB_FLEX':
      return [
        { letter: 'W', position: 'WR' },
        { letter: 'R', position: 'RB' },
        { letter: 'T', position: 'TE' },
      ];
    case 'SUPER_FLEX':
    case 'SF':
    case 'OP':
      return [
        { letter: 'W', position: 'WR' },
        { letter: 'R', position: 'RB' },
        { letter: 'T', position: 'TE' },
        { letter: 'Q', position: 'QB' },
      ];
    case 'WRRB_FLEX':
      return [
        { letter: 'W', position: 'WR' },
        { letter: 'R', position: 'RB' },
      ];
    case 'REC_FLEX':
      return [
        { letter: 'W', position: 'WR' },
        { letter: 'T', position: 'TE' },
      ];
    case 'IDP_FLEX':
      return [
        { letter: 'I', position: 'IDP' },
        { letter: 'D', position: 'IDP' },
        { letter: 'P', position: 'IDP' },
      ];
    case 'QB':
      return [{ letter: 'QB', position: 'QB' }];
    case 'RB':
      return [{ letter: 'RB', position: 'RB' }];
    case 'WR':
      return [{ letter: 'WR', position: 'WR' }];
    case 'TE':
      return [{ letter: 'TE', position: 'TE' }];
    case 'BN':
      return [{ letter: 'BN' }];
    default:
      return [{ letter: slot, position: slot }];
  }
}

function SlotDisplay({
  slot,
  empty = false,
}: {
  slot: string | null | undefined;
  empty?: boolean;
}) {
  const segments = getSlotSegments(slot);

  return (
    <span
      className={
        empty
          ? 'player-table-slot-text player-table-slot-text-empty'
          : 'player-table-slot-text'
      }
    >
      {segments.map((seg, i) => (
        <span
          key={i}
          style={{
            color: empty
              ? undefined
              : seg.position
                ? getPositionColor(seg.position)
                : 'var(--color-text-muted)',
          }}
        >
          {seg.letter}
        </span>
      ))}
    </span>
  );
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
    <div className="player-table-scroll">
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
                      <SlotDisplay slot={slot} empty />
                    </td>
                    <td
                      colSpan={redraftMeta ? 7 : 6}
                      className="player-table-empty-label"
                    >
                      Empty Starter Slot
                    </td>
                  </tr>
                ))}

              {index === firstBenchIndex ? (
                <tr className="player-table-divider">
                  <td colSpan={redraftMeta ? 8 : 7}>
                    <div className="player-table-divider-inner">
                      <span>Bench</span>
                    </div>
                  </td>
                </tr>
              ) : null}

              <tr
                className={
                  player.is_starter
                    ? 'player-table-row-starter'
                    : 'player-table-row-bench'
                }
              >
                <td className="player-table-slot-cell">
                  <SlotDisplay
                    slot={player.slot ?? (player.is_starter ? 'STARTER' : 'BN')}
                  />
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
                  {player.position}
                </td>

                <td className="player-table-team-cell">
                  {player.team ?? 'FA'}
                </td>

                <td className="player-table-num-cell">
                  {formatNumber(player.projected_points)}
                </td>

                <td className="player-table-ud-cell">
                  {player.underdog_position_rank ? (
                    player.position && player.underdog_position_rank.toUpperCase().startsWith(player.position.toUpperCase())
                      ? player.underdog_position_rank
                      : `${player.position ?? ''}${player.underdog_position_rank}`
                  ) : '—'}
                </td>

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

                {redraftMeta ? (
                  <td className="player-table-num-cell">
                    {
                      formatNumber(
                        getLeaguePlayerSelectedValue(
                          player,
                          redraftValueBasis ?? 'ktc',
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
    </div>
  );
}
