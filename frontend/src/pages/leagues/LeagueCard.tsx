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
        {league.league_name}
      </header>


      <div className="league-summary">

        <span>
          Teams: {league.rosters.length}
        </span>

      </div>



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