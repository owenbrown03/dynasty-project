import './LeaguesPage.css';

import {
  useEffect,
  useState,
} from 'react';
import { useLocation } from 'react-router';

import { useBootstrap } from '@/hooks/useBootstrap';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { Skeleton } from '@/components/feedback/Skeleton';
import { LoadingState } from '@/components/feedback/LoadingState';
import {
  useLeagueDetails,
  useLeagueOverview,
  useLeagueVisibility,
} from '@/hooks/sleeper/useLeagues';
import { notify } from '@/utils/notify';

import { LeagueSelector } from './LeagueSelector';
import { LeagueDashboard } from './LeagueDashboard';

function LeagueDetailsSkeleton() {
  return (
    <div
      className="league-card league-details-skeleton"
      role="status"
      aria-live="polite"
    >
      <span className="skeleton-sr-label">Loading league details...</span>

      <header className="league-header">
        <div className="league-header-identity">
          <Skeleton variant="circle" width={52} height={52} />

          <div className="league-details-skeleton-heading">
            <Skeleton width={54} variant="text" />
            <Skeleton width={230} variant="title" />
            <Skeleton width={132} variant="text" />
            <Skeleton width={270} variant="text" />
          </div>
        </div>
      </header>

      <section className="league-settings-panel league-overview-panel">
        <div className="league-settings-header">
          <p>League overview</p>
        </div>

        <div className="league-settings-grid">
          {
            Array.from({ length: 12 }).map((_, index) => (
              <div
                key={index}
                className="league-settings-item"
              >
                <Skeleton width={72} variant="text" />
                <Skeleton width={index % 3 === 0 ? 52 : 86} height={18} />
              </div>
            ))
          }
        </div>
      </section>

      <section className="league-detail-section">
        <div className="league-detail-header">
          <p>League notes</p>
        </div>
        <Skeleton height={92} />
        <Skeleton height={42} />
      </section>

      <div className="rosters">
        {
          Array.from({ length: 4 }).map((_, rosterIndex) => (
            <article className="roster-card league-roster-skeleton" key={rosterIndex}>
              <div className="roster-card-header">
                <div className="roster-card-identity">
                  <Skeleton width={34} height={34} radius={4} />
                  <div>
                    <Skeleton width={170} variant="title" />
                    <Skeleton width={100} variant="text" />
                  </div>
                </div>
                <div className="roster-card-rank">
                  <Skeleton width={72} variant="text" />
                  <Skeleton width={58} height={24} />
                </div>
              </div>

              <div className="roster-metrics">
                {
                  Array.from({ length: 8 }).map((_, metricIndex) => (
                    <div className="roster-metric" key={metricIndex}>
                      <Skeleton width={78} variant="text" />
                      <Skeleton width={62} height={20} />
                      <Skeleton width={34} variant="text" />
                    </div>
                  ))
                }
              </div>
            </article>
          ))
        }
      </div>
    </div>
  );
}

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
  const debouncedSelectedLeague = useDebouncedValue(
    selectedLeague,
    250,
  );

  const overview = useLeagueOverview(
    includeHidden
  );
  const visibility = useLeagueVisibility();

  const details = useLeagueDetails(
    debouncedSelectedLeague
  );

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
          {details.fetching && !details.loading && (
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
        details.data &&
        <LeagueDashboard
          league={
            details.data
          }
        />
      }

      {
        selectedLeague && details.loading && !details.data
          ? <LeagueDetailsSkeleton />
          : null
      }
    </div>
  );
};
