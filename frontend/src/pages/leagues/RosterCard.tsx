import './RosterCard.css';
import type { Roster } from '../../types';

interface Props {
  roster: Roster;
}

export function RosterCard({ roster }: Props) {
  return (
    <div className="trade-card">
      <header className="league-header">{roster.league_name}</header>      
      <div className="trade-users-row">
        {roster.players.map((player, index) => (
          <div 
            key={`${roster.league_name}-${index}`}
            className="roster-player"
          >
            {player}
          </div>
        ))}
      </div>
    </div>
  );
}