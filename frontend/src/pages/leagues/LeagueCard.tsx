import './LeagueCard.css';

import type { LeagueDetails } from '@/types';
import { RosterCard } from './RosterCard';


interface Props {
  league: LeagueDetails;
}


export function LeagueCard({
  league,
}: Props) {
  return (
    <div className="league-card">
      <header className="league-header">
        <div>
          <p className="league-header-kicker">League</p>
          <h2 className="league-title">{league.league_name}</h2>
        </div>

        <div className="league-summary">
          <span className="league-summary-stat">
            <strong>{league.rosters.length}</strong>
            <small>teams</small>
          </span>
        </div>
      </header>

      <div className="rosters">
        {league.rosters.map((roster) => (
          <RosterCard
            key={roster.roster_id}
            roster={roster}
          />
        ))}
      </div>
    </div>
  );
}
