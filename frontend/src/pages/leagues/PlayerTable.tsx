import './PlayerTable.css';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type { LeaguePlayer } from '@/types';
import { formatNumber } from '@/utils/format';
import { getPositionColor } from '@/utils/positions';

interface Props {
  players: LeaguePlayer[];
}

export function PlayerTable({ players }: Props) {
  return (
    <table className="player-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Pos</th>
          <th>Team</th>
          <th>Proj</th>
          <th>KTC</th>
          <th>FC</th>
          <th>30d</th>
          <th>UD</th>
          <th>R St</th>
          <th>R Ro</th>
          <th>D St</th>
          <th>D Ro</th>
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
            <td>{formatNumber(player.ktc_value)}</td>
            <td>{formatNumber(player.fc_value)}</td>
            <td>{formatNumber(player.fc_trend_30_day)}</td>
            <td>{player.underdog_position_rank ?? '-'}</td>
            <td>{formatNumber(player.redraft_starter_war)}</td>
            <td>{formatNumber(player.redraft_roster_war)}</td>
            <td>{formatNumber(player.dynasty_starter_war)}</td>
            <td>{formatNumber(player.dynasty_roster_war)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
