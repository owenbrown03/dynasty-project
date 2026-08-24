import { useBootstrap } from '@/hooks/useBootstrap';
import { useValuePreference } from '@/context/useValuePreference';
import { LoadingState } from '@/components/feedback/LoadingState';
import type { LeagueDetails } from '@/types';
import type { ValueBasis } from '@/types';

import './LeagueDashboard.css';

import { LeagueCard } from './LeagueCard';
import { LeagueWarSeasonChart } from './LeagueWarSeasonChart';
import { AdvisorPanel } from './AdvisorPanel';


interface Props {
  league: LeagueDetails | null;
  leagueFallback: {
    league_id: string;
    league_name: string;
  };
  activeTab: 'overview' | 'analytics' | 'advisor';
  onTabChange: (
    tab: 'overview' | 'analytics' | 'advisor',
  ) => void;
}

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
  leagueFallback,
  activeTab,
  onTabChange,
}: Props) {
  const bootstrap = useBootstrap();
  const valuePreference = useValuePreference();
  const rosterSortBasis = normalizeLeagueSortBasis(
    valuePreference.preference,
  );

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
              onTabChange('overview');
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
              onTabChange('analytics');
            }}
          >
            Analytics
          </button>

          <button
            type="button"
            className={
              activeTab === 'advisor'
                ? 'league-dashboard-tab active'
                : 'league-dashboard-tab'
            }
            onClick={() => {
              onTabChange('advisor');
            }}
          >
            AI Advisor
          </button>
        </div>

      </div>

      {
        activeTab === 'overview'
          ? (
            league
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
              : <LoadingState label="Loading league details..." />
          )
          : activeTab === 'analytics'
            ? (
              league
                ? (
                  <LeagueWarSeasonChart
                    league={league}
                  />
                )
                : <LoadingState label="Loading league details..." />
            )
            : (
              <AdvisorPanel
                leagueId={
                  league?.league_id ?? leagueFallback.league_id
                }
                leagueName={
                  league?.league_name ?? leagueFallback.league_name
                }
              />
            )
      }
    </div>
  );
}
