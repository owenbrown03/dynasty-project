import './OrphanCard.css';
import type { Orphan } from '../../types';

interface Props {
  orphan: Orphan;
}

export function OrphanCard({ orphan }: Props) {
  return (
    <div className="orphan-card">
      <header className="league-header">
        <span className="header-line-1">{orphan.league_name}</span>
        <span className="header-line-2">{orphan.roster_name}</span>
      </header>      
      <div className="orphan-players-row">
        {orphan.players.map((player, index) => (
          <div 
            key={`${orphan.league_name}-${index}`}
            className="orphan-player"
          >
            {player}
          </div>
        ))}
      </div>
    </div>
  );
}