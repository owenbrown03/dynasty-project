import './PlayerTable.css';
import type { LeaguePlayer } from '@/types';
import { formatNumber } from '@/utils/format';

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
          <th>Starter WAR</th>
          <th>Roster WAR</th>
        </tr>
      </thead>

      <tbody>
        {players.map((player) => (
          <tr key={player.player_id}>
            <td>{player.name}</td>
            <td>{player.position}</td>
            <td>{player.team ?? '-'}</td>
            <td>{formatNumber(player.starter_war)}</td>
            <td>{formatNumber(player.roster_war)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}