import './LeaguesPage.css';

import { useState } from 'react';
import { useLocation } from 'react-router';

import { useLeagueDetails, useLeagueOverview } from '@/hooks/sleeper/useLeagues';

import { LeagueSelector } from './LeagueSelector';
import { LeagueDashboard } from './LeagueDashboard';

export const LeaguesPage = () => {


  const location = useLocation();

  const initialLeagueId =
    location.state?.leagueId;

  const [
    selectedLeague,
    setSelectedLeague
  ] = useState<string>(
    initialLeagueId
  );

  const overview = useLeagueOverview();

  const details = useLeagueDetails(
    selectedLeague
  );



  return (

    <div className="leagues-container">


      <LeagueSelector

        leagues={
          overview.data
        }

        selectedLeague={
          selectedLeague
        }

        onSelect={
          setSelectedLeague
        }

      />



      {
        details.data &&

        <LeagueDashboard
          league={
            details.data
          }
        />

      }


    </div>

  );

};