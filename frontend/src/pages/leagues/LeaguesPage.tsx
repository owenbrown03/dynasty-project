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
      <section className="leagues-page-header">
        <div>
          <p className="page-eyebrow">Leagues</p>
          <h1 className="leagues-page-title">League details</h1>
          <p className="leagues-page-description">
            Review roster strength, WAR distribution, and player composition for
            each synced league.
          </p>
        </div>
      </section>

      <section className="leagues-selector-panel">
        <div className="leagues-selector-copy">
          <p className="leagues-selector-label">League selector</p>
          <p className="leagues-selector-hint">
            Choose a league to inspect its current roster breakdown.
          </p>
        </div>

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
      </section>

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
