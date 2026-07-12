import './LeaguesPage.css';

import {
  useEffect,
  useState,
} from 'react';
import { useLocation } from 'react-router';

import { useBootstrap } from '@/hooks/useBootstrap';
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

  const overview = useLeagueOverview(
    includeHidden
  );
  const visibility = useLeagueVisibility();

  const details = useLeagueDetails(
    selectedLeague
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
            Choose a visible current league, or turn on hidden leagues to manage archived leftovers.
          </p>
        </div>

        <div className="leagues-selector-controls">
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
