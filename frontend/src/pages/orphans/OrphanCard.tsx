import './OrphanCard.css';
import type { Orphan } from '../../types';

interface Props {
  orphan: Orphan;
}

export function OrphanCard({ orphan }: Props) {
  return (
    <div className="orphan-card">
      <header className="orphan-card-header">
        <div>
          <p className="orphan-card-kicker">League</p>
          <h2 className="orphan-league-name">{orphan.league_name}</h2>
        </div>

        <div className="orphan-roster-name">{orphan.roster_name}</div>
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
