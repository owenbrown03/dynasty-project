import './LeagueDashboard.css';

import type { LeagueDetails } from '@/types';
import { LeagueCard } from './LeagueCard';
import { LeagueWarChart } from './LeagueWarChart';


interface Props {
  league: LeagueDetails;
}


export function LeagueDashboard({
  league,
}: Props) {


  return (
    <div className="league-dashboard">
      <LeagueWarChart
        league={league}
      />

      <LeagueCard
        league={league}
      />

    </div>
  );
}
