import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import { AlertTriangle, HandCoins, Search } from 'lucide-react';

import { LoadingState } from '@/components/feedback/LoadingState';
import {
  useAvailableWaiverPlayers,
  useWaiverLeagueOptions,
} from '@/hooks/sleeper/useWaivers';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

import type {
  ValueBasis,
  WaiverAvailablePlayer,
} from '@/types';

import { AvailableLeagueSelector } from './AvailableLeagueSelector';
import { AvailablePlayerClaimModal } from './AvailablePlayerClaimModal';
import { AvailablePlayersTable } from './AvailablePlayersTable';


interface AvailablePlayersTabProps {
  valueBasis: ValueBasis;
  selectedLeagueId: string | undefined;
  onSelectedLeagueIdChange: (
    leagueId: string | undefined,
  ) => void;
}


export const AvailablePlayersTab = ({
  valueBasis,
  selectedLeagueId,
  onSelectedLeagueIdChange,
}: AvailablePlayersTabProps) => {
  const [
    page,
    setPage,
  ] = useState(1);
  const [
    pageSize,
    setPageSize,
  ] = useState(50);
  const [
    claimPlayer,
    setClaimPlayer,
  ] = useState<WaiverAvailablePlayer | null>(
    null,
  );

  const {
    canWrite,
  } = useSleeperConnection();

  const leagues = useWaiverLeagueOptions();

  useEffect(() => {
    if (selectedLeagueId) {
      const hasSelectedLeague = leagues.data.some(
        (league) => (
          league.league_id === selectedLeagueId
        ),
      );

      if (!hasSelectedLeague) {
        onSelectedLeagueIdChange(
          undefined,
        );
      }
    }
  }, [
    leagues.data,
    onSelectedLeagueIdChange,
    selectedLeagueId,
  ]);

  const selectedLeague = useMemo(
    () => (
      leagues.data.find(
        (league) => (
          league.league_id === selectedLeagueId
        ),
      )
    ),
    [
      leagues.data,
      selectedLeagueId,
    ],
  );

  const availablePlayers = useAvailableWaiverPlayers(
    selectedLeagueId,
    valueBasis,
    page,
    pageSize,
  );

  useEffect(() => {
    setPage(1);
  }, [
    selectedLeagueId,
    valueBasis,
    pageSize,
  ]);

  if (leagues.loading) {
    return (
      <LoadingState
        label="Loading your leagues..."
        className="waivers-loading-state"
      />
    );
  }

  if (leagues.error) {
    return (
      <div className="empty-state">
        <AlertTriangle size={32} className="empty-state-icon" />
        <p className="empty-state-title">Unable to load leagues</p>
        <p className="empty-state-message">
          Check your Sleeper connection and try again.
        </p>
      </div>
    );
  }

  if (leagues.data.length === 0) {
    return (
      <div className="empty-state">
        <HandCoins size={32} className="empty-state-icon" />
        <p className="empty-state-title">No waiver leagues</p>
        <p className="empty-state-message">
          Sync your Sleeper leagues and try again.
        </p>
      </div>
    );
  }

  return (
    <section className="available-players-section">
      <div className="available-players-toolbar">
        <div>
          <h2>
            Available Players
          </h2>

          <p>
            Full available QB, RB, WR, and TE pool
            across your visible leagues, sorted by
            your selected value basis.
          </p>
        </div>

        <AvailableLeagueSelector
          leagues={leagues.data}
          selectedLeagueId={selectedLeagueId}
          onChange={(leagueId) => {
            onSelectedLeagueIdChange(
              leagueId,
            );
            setPage(1);
            setClaimPlayer(null);
          }}
        />
      </div>

      {
        availablePlayers.loading
          ? (
            <LoadingState
              label="Calculating available player values..."
              className="waivers-loading-state"
            />
          )
          : null
      }

      {
        availablePlayers.fetching
          && !availablePlayers.loading
          ? (
            <div className="waivers-refreshing">
              Updating player values...
            </div>
          )
          : null
      }

      {
        availablePlayers.error
          ? (
            <div className="empty-state">
              <Search size={32} className="empty-state-icon" />
              <p className="empty-state-title">Unable to load players</p>
              <p className="empty-state-message">
                Try selecting the league again.
              </p>
            </div>
          )
          : null
      }

      {
        availablePlayers.data
          ? (
            <>
              {(() => {
                const data = availablePlayers.data;

                return (
                  <>
              <div className="available-players-summary">
                <span>
                  {
                    data
                      .is_all_leagues
                      ? 'All visible leagues'
                      : selectedLeague?.league_name
                  }
                </span>

                <span>
                  {
                    data.total_players
                      .toLocaleString()
                  }
                  {' '}available players
                </span>

                <span>
                  Ranked by {data.value_label}
                </span>
              </div>

              <div className="available-pagination-toolbar">
                <label className="available-page-size-selector">
                  <span>Rows</span>

                  <select
                    value={pageSize}
                    onChange={(event) => {
                      setPageSize(
                        Number(
                          event.target.value,
                        ),
                      );
                    }}
                  >
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                    <option value={150}>150</option>
                  </select>
                </label>

                <div className="available-pagination-status">
                  Page {data.page}
                  {' of '}
                  {data.total_pages}
                </div>

                <div className="available-pagination-actions">
                  <button
                    type="button"
                    className="button-secondary"
                    disabled={
                      data.page <= 1
                    }
                    onClick={() => {
                      setPage(
                        data.page - 1,
                      );
                    }}
                  >
                    Previous
                  </button>

                  <button
                    type="button"
                    className="button-secondary"
                    disabled={
                      data.page
                      >= data.total_pages
                    }
                    onClick={() => {
                      setPage(
                        data.page + 1,
                      );
                    }}
                  >
                    Next
                  </button>
                </div>
              </div>

              <AvailablePlayersTable
                data={data}
                canWrite={canWrite}
                onClaim={setClaimPlayer}
              />
                  </>
                );
              })()}
            </>
          )
          : null
      }

      {
        claimPlayer
          ? (
            <AvailablePlayerClaimModal
              league={{
                league_id: claimPlayer.league_id,
                league_name: claimPlayer.league_name,
                league_avatar:
                  claimPlayer.league_avatar,
                roster_id: claimPlayer.roster_id,
                roster_size: claimPlayer.roster_size,
                roster_capacity:
                  claimPlayer.roster_capacity,
                roster_spots_available:
                  claimPlayer.roster_spots_available,
                faab_remaining:
                  claimPlayer.faab_remaining,
                faab_percent_remaining:
                  claimPlayer.faab_percent_remaining,
              }}
              addPlayer={claimPlayer}
              valueBasis={valueBasis}
              onClose={() => {
                setClaimPlayer(null);
              }}
            />
          )
          : null
      }
    </section>
  );
};
