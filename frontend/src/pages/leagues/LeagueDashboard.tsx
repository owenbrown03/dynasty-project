import { useEffect, useState } from 'react';

import { useBootstrap } from '@/hooks/useBootstrap';
import { useValuePreference } from '@/context/useValuePreference';
import type { LeagueDetails } from '@/types';
import type { ValueBasis } from '@/types';

import './LeagueDashboard.css';

import { LeagueCard } from './LeagueCard';
import { LeagueWarSeasonChart } from './LeagueWarSeasonChart';


interface Props {
  league: LeagueDetails;
}

type LeagueDashboardTab =
  | 'overview'
  | 'analytics';

function normalizeLeagueSortBasis(
  valueBasis: ValueBasis,
): ValueBasis {
  if (
    valueBasis === 'dynasty_starter_war'
    || valueBasis === 'dynasty_roster_war'
    || valueBasis === 'redraft_starter_war'
    || valueBasis === 'redraft_roster_war'
  ) {
    return 'sleeper_war';
  }

  if (valueBasis === 'adp') {
    return 'ktc';
  }

  return valueBasis;
}


export function LeagueDashboard({
  league,
}: Props) {
  const bootstrap = useBootstrap();
  const valuePreference = useValuePreference();
  const [activeTab, setActiveTab] = useState<LeagueDashboardTab>('overview');
  const [rosterSortBasis, setRosterSortBasis] = useState<ValueBasis>(
    normalizeLeagueSortBasis(
      valuePreference.preference,
    ),
  );

  useEffect(() => {
    setRosterSortBasis(
      normalizeLeagueSortBasis(
        valuePreference.preference,
      ),
    );
  }, [valuePreference.preference]);

  return (
    <div className="league-dashboard">
      <div className="league-dashboard-toolbar">
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

        <label className="league-dashboard-sort-control">
          <span>Roster rank</span>
          <select
            value={rosterSortBasis}
            onChange={(event) => {
              setRosterSortBasis(
                event.target.value as ValueBasis,
              );
            }}
          >
            <option value="ktc">KTC</option>
            <option value="fantasycalc">FantasyCalc</option>
            <option value="sleeper_war">Sleeper WAR</option>
            {
              bootstrap.data?.authenticated
                ? (
                  <option value="my_war">My WAR</option>
                )
                : null
            }
          </select>
        </label>
      </div>

      {
        activeTab === 'overview'
          ? (
            <LeagueCard
              league={league}
              rosterSortBasis={rosterSortBasis}
              warValueSettings={bootstrap.data?.war_value_settings ?? {
                sleeper_projection: {
                  timeframe: 'dynasty',
                  scope: 'roster',
                },
                my: {
                  timeframe: 'dynasty',
                  scope: 'roster',
                },
              }}
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
