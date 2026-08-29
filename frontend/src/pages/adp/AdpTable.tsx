import type { ADPPlayerRow } from '@/types';
import { TeamBadge } from '@/components/players/TeamBadge';

import { formatPercent } from './adp.utils';

interface AdpTableProps {
  players: ADPPlayerRow[];
}

export function AdpTable({
  players,
}: AdpTableProps) {
  return (
    <div className="adp-table-wrap">
      <table className="adp-table">
        <thead>
          <tr>
            <th>ADP</th>
            <th>Player</th>
            <th>Pos</th>
            <th>Team</th>
            <th>Median</th>
            <th>Range</th>
            <th>Std Dev</th>
            <th>Drafts</th>
            <th>Selection rate</th>
          </tr>
        </thead>
        <tbody>
          {players.map((player) => (
            <tr key={player.player_id}>
              <td>{player.overall_adp.toFixed(2)}</td>
              <td>{player.name}</td>
              <td>{player.position ?? '—'}</td>
              <td>
                <TeamBadge team={player.team} size="sm" fallbackText="—" />
              </td>
              <td>{player.median_pick.toFixed(1)}</td>
              <td>{player.min_pick} - {player.max_pick}</td>
              <td>{player.standard_deviation?.toFixed(2) ?? '—'}</td>
              <td>{player.draft_count.toLocaleString()}</td>
              <td>{formatPercent(player.selection_rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
