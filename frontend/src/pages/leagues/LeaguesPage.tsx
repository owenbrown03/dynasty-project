import './LeaguesPage.css';

import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useLocation, useSearchParams } from 'react-router';

import { useBootstrap } from '@/hooks/useBootstrap';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { LoadingState } from '@/components/feedback/LoadingState';
import {
  useLeagueDetails,
  useLeagueOverview,
  useLeagueVisibility,
} from '@/hooks/sleeper/useLeagues';
import { notify } from '@/utils/notify';

import { LeagueSelector } from './LeagueSelector';
import { LeagueDashboard } from './LeagueDashboard';

export const LeaguesPage = () => {
  const location = useLocation();
  const initialLeagueId =
    location.state?.leagueId;
  const bootstrap = useBootstrap();
  const [
    selectedLeague,
    setSelectedLeague
  ] = useState<string | undefined>(
    initialLeagueId
  );
  const [
    includeHidden,
    setIncludeHidden
  ] = useState(false);
  const [searchParams, setSearchParams] =
    useSearchParams();
  const debouncedSelectedLeague = useDebouncedValue(
    selectedLeague,
    250,
  );

  const activeTab = useMemo<
    'overview' | 'analytics' | 'advisor'
  >(() => {
    const tab = searchParams.get('tab');

    if (
      tab === 'overview'
      || tab === 'analytics'
      || tab === 'advisor'
    ) {
      return tab;
    }

    return 'overview';
  }, [searchParams]);

  const setActiveTab = (
    nextTab: 'overview' | 'analytics' | 'advisor',
  ) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', nextTab);
    setSearchParams(next);
  };

  const overview = useLeagueOverview(
    includeHidden
  );
  const visibility = useLeagueVisibility();

  const cheapDetails = useLeagueDetails(
    debouncedSelectedLeague,
    true,
  );
  const fullDetails = useLeagueDetails(
    debouncedSelectedLeague,
    false,
  );

  const displayData = fullDetails.data ?? cheapDetails.data;
  const isLoading = cheapDetails.loading;
  const isFetching = fullDetails.fetching;

  const selectedLeagueEntry =
    overview.data.find(
      (league) =>
        league.league_id === selectedLeague
    ) ?? null;

  useEffect(() => {
    if (!overview.data.length) {
      return;
    }

    if (
      selectedLeague
      && overview.data.some(
        (league) =>
          league.league_id === selectedLeague
      )
    ) {
      return;
    }

    setSelectedLeague(
      overview.data[0].league_id
    );
  }, [
    overview.data,
    selectedLeague,
  ]);

  const handleVisibilityChange =
    async (
      hidden: boolean
    ) => {
      if (!selectedLeagueEntry) {
        return;
      }

      try {
        await visibility.setLeagueVisibility({
          leagueId:
            selectedLeagueEntry.league_id,
          payload: {
            hidden,
          },
        });

        notify.success(
          hidden
            ? 'League hidden from current selectors.'
            : 'League restored to current selectors.',
        );

        if (hidden && !includeHidden) {
          setSelectedLeague(undefined);
        }
      } catch {
        notify.error(
          'Unable to update league visibility.',
        );
      }
    };

  return (
    <div className="leagues-container">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Leagues</p>
          <h1 className="page-title">League details</h1>
          <p className="page-description">
            Review roster strength, WAR distribution, and player composition for
            each synced league.
          </p>
          {isFetching && !isLoading && (
            <LoadingState label="Updating league details..." inline className="leagues-refresh-indicator" />
          )}
        </div>
      </section>

      <section className="leagues-selector-panel">
        <div className="leagues-selector-copy">
          <p className="leagues-selector-label">League selector</p>
          <p className="leagues-selector-hint">
            Choose a visible current league, or turn on hidden leagues to manage archived leftovers.
          </p>
        </div>

        <div className="leagues-selector-controls">
          <div className="leagues-selector-top-row">
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
              bootstrap.data?.authenticated
              && selectedLeagueEntry
                ? (
                  <button
                    type="button"
                    className="button-secondary leagues-visibility-button"
                    disabled={visibility.saving}
                    onClick={() => {
                      void handleVisibilityChange(
                        !selectedLeagueEntry.is_hidden
                      );
                    }}
                  >
                    {
                      visibility.saving
                        ? 'Saving...'
                        : selectedLeagueEntry.is_hidden
                          ? 'Unhide league'
                          : 'Hide league'
                    }
                  </button>
                )
                : null
            }
          </div>

          <label className="leagues-selector-toggle">
            <input
              type="checkbox"
              checked={includeHidden}
              onChange={(
                event
              ) =>
                setIncludeHidden(
                  event.target.checked
                )
              }
            />
            <span>Show hidden leagues</span>
          </label>
        </div>
      </section>

      {
        debouncedSelectedLeague && (
          <LeagueDashboard
            league={displayData ?? null}
            leagueFallback={{
              league_id: debouncedSelectedLeague,
              league_name:
                selectedLeagueEntry?.league_name ?? 'League',
            }}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        )
      }
    </div>
  );
};
