import { useState } from 'react';

import type { LeagueDetails } from '@/types';

import './LeagueDashboard.css';

import { LeagueCard } from './LeagueCard';
import { LeagueWarSeasonChart } from './LeagueWarSeasonChart';


interface Props {
  league: LeagueDetails;
}

type LeagueDashboardTab =
  | 'overview'
  | 'analytics';


export function LeagueDashboard({
  league,
}: Props) {
  const [activeTab, setActiveTab] = useState<LeagueDashboardTab>('overview');

  return (
    <div className="league-dashboard">
      <div className="league-dashboard-tabs" role="tablist" aria-label="League dashboard tabs">
        <button
          type="button"
          className={
            activeTab === 'overview'
              ? 'league-dashboard-tab active'
              : 'league-dashboard-tab'
          }
          onClick={() => {
            setActiveTab('overview');
          }}
        >
          Overview
        </button>

        <button
          type="button"
          className={
            activeTab === 'analytics'
              ? 'league-dashboard-tab active'
              : 'league-dashboard-tab'
          }
          onClick={() => {
            setActiveTab('analytics');
          }}
        >
          Analytics
        </button>
      </div>

      {
        activeTab === 'overview'
          ? (
            <LeagueCard
              league={league}
            />
          )
          : (
            <LeagueWarSeasonChart
              league={league}
            />
          )
      }
    </div>
  );
}
