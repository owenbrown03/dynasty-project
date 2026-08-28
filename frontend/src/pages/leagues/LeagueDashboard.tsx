import { useBootstrap } from '@/hooks/useBootstrap';
import { useValuePreference } from '@/context/useValuePreference';
import { LoadingState } from '@/components/feedback/LoadingState';
import type { LeagueDetails } from '@/types';
import type { ValueBasis } from '@/types';

import './LeagueDashboard.css';

import { LeagueCard } from './LeagueCard';
import { LeagueRosterBarChart } from './LeagueRosterBarChart';
import { LeagueWarSeasonChart } from './LeagueWarSeasonChart';
import { AdvisorPanel } from './AdvisorPanel';


interface Props {
  league: LeagueDetails | null;
  isFocused?: boolean;
  leagueFallback: {
    league_id: string;
    league_name: string;
  };
  activeTab: 'overview' | 'charts' | 'analytics' | 'advisor';
  onTabChange: (
    tab: 'overview' | 'charts' | 'analytics' | 'advisor',
  ) => void;
}

function normalizeLeagueSortBasis(
  valueBasis: ValueBasis,
): ValueBasis {
  // Every pool basis now resolves directly; legacy parameterized
  // aliases are gone.
  return valueBasis;
}


export function LeagueDashboard({
  league,
  isFocused,
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
    <div
      className={
        isFocused
          ? 'league-dashboard focused'
          : 'league-dashboard'
      }
    >
      <div className="league-dashboard-toolbar">
        <div className="page-tabs" role="tablist" aria-label="League dashboard tabs">
          <button
            type="button"
            className={
              activeTab === 'overview'
                ? 'page-tab active'
                : 'page-tab'
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
              activeTab === 'charts'
                ? 'page-tab active'
                : 'page-tab'
            }
            onClick={() => {
              onTabChange('charts');
            }}
          >
            Bar Chart
          </button>

          <button
            type="button"
            className={
              activeTab === 'analytics'
                ? 'page-tab active'
                : 'page-tab'
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
                ? 'page-tab active'
                : 'page-tab'
            }
            onClick={() => {
              onTabChange('advisor');
            }}
          >
            Roster Lab
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
          : activeTab === 'charts'
            ? (
              league
                ? (
                  <LeagueRosterBarChart
                    league={league}
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
