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

interface Props {
  players: LeaguePlayer[];
  valueBasis: ValueBasis;
  warValueSettings: WarValueSettings;
}

export function PlayerTable({
  players,
  valueBasis,
  warValueSettings,
}: Props) {
  const valueLabel = getValueBasisLabel(
    valueBasis,
  );

  return (
    <table className="player-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Pos</th>
          <th>Team</th>
          <th>Proj</th>
          <th>UD</th>
          <th>{valueLabel}</th>
        </tr>
      </thead>

      <tbody>
        {players.map((player) => (
          <tr
            key={player.player_id}
            className={
              player.is_starter
                ? 'player-table-row-starter'
                : undefined
            }
          >
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
          </tr>
        ))}
      </tbody>
    </table>
  );
}
