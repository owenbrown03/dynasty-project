import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import { AlertTriangle, HandCoins, Search } from 'lucide-react';

import { PaginationToolbar } from '@/components/controls/PaginationToolbar';
import { Skeleton } from '@/components/feedback/Skeleton';
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

function AvailablePlayersSkeleton({
  mode,
}: {
  mode: 'leagues' | 'players';
}) {
  if (mode === 'players') {
    return (
      <div
        className="available-players-loading-shell"
        role="status"
        aria-live="polite"
      >
        <span className="skeleton-sr-label">
          Calculating available player values...
        </span>

        <div className="available-players-summary">
          <Skeleton width={140} variant="text" />
          <Skeleton width={130} variant="text" />
          <Skeleton width={160} variant="text" />
        </div>

        <Skeleton width={210} height={40} />

        <AvailablePlayersTableSkeleton />
      </div>
    );
  }

  return (
    <section
      className="available-players-section"
      role="status"
      aria-live="polite"
    >
      <span className="skeleton-sr-label">
        {
          mode === 'leagues'
            ? 'Loading your leagues...'
            : 'Calculating available player values...'
        }
      </span>

      <div className="available-players-toolbar">
        <div>
          <Skeleton width={180} variant="title" />
          <Skeleton width="min(520px, 100%)" variant="text" />
        </div>
        <Skeleton width={260} height={42} />
      </div>

      <div className="available-players-summary">
        <Skeleton width={140} variant="text" />
        <Skeleton width={130} variant="text" />
        <Skeleton width={160} variant="text" />
      </div>

      <Skeleton width={210} height={40} />

      <AvailablePlayersTableSkeleton />
    </section>
  );
}

function AvailablePlayersTableSkeleton() {
  return (
    <div className="available-players-table-wrapper">
      <table className="available-players-table available-players-table-skeleton">
        <thead>
          <tr>
            {
              ['Player', 'Pos', 'Team', 'Leagues', 'Age', 'Value', 'Action'].map((label) => (
                <th key={label}>{label}</th>
              ))
            }
          </tr>
        </thead>
        <tbody>
          {
            Array.from({ length: 8 }).map((_, rowIndex) => (
              <tr key={rowIndex}>
                <td className="available-player-name-cell">
                  <div className="player-with-avatar">
                    <Skeleton width={34} height={34} radius={4} />
                    <div className="player-with-avatar-copy">
                      <Skeleton width={150} variant="title" />
                      <Skeleton width={58} variant="text" />
                    </div>
                  </div>
                </td>
                <td><Skeleton width={32} variant="text" /></td>
                <td><Skeleton width={40} variant="text" /></td>
                <td><Skeleton width={140} variant="text" /></td>
                <td><Skeleton width={34} variant="text" /></td>
                <td><Skeleton width={82} height={20} /></td>
                <td><Skeleton width={102} height={34} /></td>
              </tr>
            ))
          }
        </tbody>
      </table>
    </div>
  );
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
      <AvailablePlayersSkeleton mode="leagues" />
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
            <AvailablePlayersSkeleton mode="players" />
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

              <PaginationToolbar
                page={data.page}
                pageSize={pageSize}
                totalPages={data.total_pages}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
              />

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
                league_id:
                  claimPlayer.league_id ?? '',
                league_name:
                  claimPlayer.league_name ?? '',
                league_avatar:
                  claimPlayer.league_avatar,
                roster_id:
                  claimPlayer.roster_id ?? 0,
                roster_size:
                  claimPlayer.roster_size ?? 0,
                roster_capacity:
                  claimPlayer.roster_capacity
                  ?? 0,
                roster_spots_available:
                  claimPlayer.roster_spots_available
                  ?? 0,
                faab_remaining:
                  claimPlayer.faab_remaining
                  ?? 0,
                faab_percent_remaining:
                  claimPlayer.faab_percent_remaining
                  ?? 0,
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
