import './LeagueDashboard.css';

import type { LeagueDetails } from '@/types';
import { LeagueCard } from './LeagueCard';
import { LeagueWarHistoryChart } from './LeagueWarHistoryChart';
import { LeagueWarChart } from './LeagueWarChart';


interface Props {
  league: LeagueDetails;
}


export function LeagueDashboard({
  league,
}: Props) {


  return (
    <div className="league-dashboard">
      <LeagueWarHistoryChart
        league={league}
      />

      <LeagueWarChart
        league={league}
      />

      <LeagueCard
        league={league}
      />

    </div>
  );
}
