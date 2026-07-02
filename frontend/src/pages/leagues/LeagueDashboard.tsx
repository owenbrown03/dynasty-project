import './LeagueDashboard.css';

import type { LeagueDetails } from '@/types';
import { LeagueCard } from './LeagueCard';


interface Props {
  league: LeagueDetails;
}


export function LeagueDashboard({
  league,
}: Props) {


  return (
    <div className="league-dashboard">

      <LeagueCard
        league={league}
      />

    </div>
  );
}