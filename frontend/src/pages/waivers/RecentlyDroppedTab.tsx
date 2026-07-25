import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  AlertTriangle,
  Clock3,
  HandCoins,
} from 'lucide-react';

import { PaginationToolbar } from '@/components/controls/PaginationToolbar';
import { Skeleton } from '@/components/feedback/Skeleton';
import { LeagueAvatar } from '@/components/leagues/LeagueAvatar';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useRecentlyDroppedPlayers } from '@/hooks/sleeper/useWaivers';

import type {
  ValueBasis,
  WaiverAvailablePlayer,
  WaiverLeagueOption,
  WaiverRecentlyDroppedPlayer,
} from '@/types';

import { AvailablePlayerClaimModal } from './AvailablePlayerClaimModal';
import { formatSelectedValue } from './waiver.formatters';


interface RecentlyDroppedTabProps {
  valueBasis: ValueBasis;
}


function formatDroppedAt(
  timestampMs: number,
) {
  return new Intl.DateTimeFormat(
    undefined,
    {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    },
  ).format(
    new Date(timestampMs),
  );
}

function RecentDropsSkeleton() {
  return (
    <section
      className="available-players-section"
      role="status"
      aria-live="polite"
    >
      <span className="skeleton-sr-label">Loading recently dropped players...</span>

      <div className="available-players-toolbar">
        <div>
          <Skeleton width={190} variant="title" />
          <Skeleton width="min(520px, 100%)" variant="text" />
        </div>

        <div className="available-players-summary">
          <Skeleton width={86} variant="text" />
          <Skeleton width={180} variant="text" />
        </div>
      </div>

      <Skeleton width={240} height={40} />

      <div className="recent-drops-list">
        {
          Array.from({ length: 5 }).map((_, index) => (
            <article className="recent-drop-card" key={index}>
              <div className="recent-drop-main">
                <div className="recent-drop-card-header">
                  <div className="player-with-avatar">
                    <Skeleton width={40} height={40} radius={4} />
                    <div className="player-with-avatar-copy">
                      <Skeleton width={150} variant="title" />
                      <Skeleton width={76} variant="text" />
                    </div>
                  </div>
                </div>

                <div className="recent-drop-meta-row">
                  <div className="recent-drop-league">
                    <Skeleton width={32} height={32} radius={4} />
                    <div className="recent-drop-league-copy">
                      <Skeleton width={170} variant="title" />
                      <Skeleton width={116} variant="text" />
                    </div>
                  </div>
                </div>

                <div className="recent-drop-footer">
                  <Skeleton width={220} height={36} />
                </div>
              </div>

              <div className="recent-drop-side">
                <div className="recent-drop-value">
                  <Skeleton width={132} variant="text" />
                  <Skeleton width={56} height={24} />
                </div>
                <div className="recent-drop-time">
                  <Skeleton width={120} variant="text" />
                </div>
                <Skeleton width={128} height={42} />
              </div>
            </article>
          ))
        }
      </div>
    </section>
  );
}


export const RecentlyDroppedTab = ({
  valueBasis,
}: RecentlyDroppedTabProps) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [sortBy, setSortBy] = useState<'value' | 'recency'>(
    'recency',
  );
  const [claimPlayer, setClaimPlayer] = useState<WaiverRecentlyDroppedPlayer | null>(
    null,
  );
  const recentDrops = useRecentlyDroppedPlayers(
    valueBasis,
    page,
    pageSize,
    sortBy,
  );
  const {
    canWrite,
  } = useSleeperConnection();

  useEffect(() => {
    setPage(1);
  }, [
    valueBasis,
    pageSize,
    sortBy,
  ]);

  const modalLeague = useMemo<WaiverLeagueOption | null>(
    () => {
      if (!claimPlayer) {
        return null;
      }

      return {
        league_id: claimPlayer.league_id,
        league_name: claimPlayer.league_name,
        league_avatar: claimPlayer.league_avatar,
        roster_id: claimPlayer.roster_id,
        roster_size: 0,
        roster_capacity: 0,
        roster_spots_available: claimPlayer.roster_spots_available,
        faab_remaining: claimPlayer.faab_remaining,
        faab_percent_remaining: claimPlayer.faab_percent_remaining,
      };
    },
    [claimPlayer],
  );

  const modalPlayer = useMemo<WaiverAvailablePlayer | null>(
    () => {
      if (!claimPlayer) {
        return null;
      }

      return {
        ...claimPlayer,
        roster_size: 0,
        roster_capacity: 0,
        can_submit_claim:
          claimPlayer.can_submit_claim,
        claim_blocked_reason:
          claimPlayer.claim_blocked_reason,
        league_count: 1,
        league_availability: [],
      };
    },
    [claimPlayer],
  );

  if (recentDrops.loading) {
    return (
      <RecentDropsSkeleton />
    );
  }

  if (recentDrops.error) {
    return (
      <div className="empty-state">
        <AlertTriangle size={32} className="empty-state-icon" />
        <p className="empty-state-title">Unable to load recent drops</p>
        <p className="empty-state-message">
          Check your Sleeper connection and try again.
        </p>
      </div>
    );
  }

  if (!recentDrops.data || recentDrops.data.players.length === 0) {
    return (
      <div className="empty-state">
        <HandCoins size={32} className="empty-state-icon" />
        <p className="empty-state-title">No recent drops</p>
        <p className="empty-state-message">
          Once players are dropped in your visible leagues, they will show up here.
        </p>
      </div>
    );
  }

  const data = recentDrops.data;

  return (
    <section className="available-players-section">
      <div className="available-players-toolbar">
        <div>
          <h2>
            Recently Dropped
          </h2>

          <p>
            Claim players from the latest completed drops across your visible leagues.
          </p>
        </div>

        <div className="available-players-summary">
          <span>
            {data.total_players.toLocaleString()}
            {' '}players
          </span>

          <span>
            {
              sortBy === 'value'
                ? `Ranked by ${data.value_label}`
                : 'Ranked by most recent drop'
            }
          </span>
        </div>
      </div>

      <PaginationToolbar
        page={data.page}
        pageSize={pageSize}
        totalPages={data.total_pages}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        leadingControls={(
          <label className="available-page-size-selector">
            <span>Sort</span>

            <select
              value={sortBy}
              onChange={(event) => {
                setSortBy(
                  event.target.value as 'value' | 'recency',
                );
              }}
            >
              <option value="value">Value</option>
              <option value="recency">Recency</option>
            </select>
          </label>
        )}
      />

      {
        data.sync_requested
          ? (
            <div className="waivers-refreshing">
              Daily league sync queued. This list will refresh as new drops land.
            </div>
          )
          : null
      }

      <div className="recent-drops-list">
        {
          data.players.map((player) => {
            const claimDisabledReason = (
              !canWrite
                ? 'Connect Sleeper write access to claim players.'
                : player.claim_blocked_reason
            );

            return (
              <article
                key={`${player.transaction_id}-${player.player_id}`}
                className="recent-drop-card"
              >
                <div className="recent-drop-main">
                  <div className="recent-drop-card-header">
                    <div className="player-with-avatar">
                      <PlayerAvatar
                        playerId={player.player_id}
                        name={player.name}
                        size="md"
                      />

                      <div className="player-with-avatar-copy">
                        <strong>{player.name}</strong>
                        <span>
                          {[player.position, player.team].filter(Boolean).join(' · ')}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="recent-drop-meta-row">
                    <div className="recent-drop-league">
                      <LeagueAvatar
                        avatarId={player.league_avatar}
                        name={player.league_name}
                        size="sm"
                      />

                      <div className="recent-drop-league-copy">
                        <strong>{player.league_name}</strong>
                        <span>
                          FAAB ${player.faab_remaining}
                          {' · '}
                          {player.faab_percent_remaining.toFixed(1)}% left
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="recent-drop-footer">
                    {
                      claimDisabledReason
                        ? (
                          <span className="waiver-read-only recent-drop-status">
                            {claimDisabledReason}
                          </span>
                        )
                        : (
                          <span className="waiver-read-only recent-drop-status recent-drop-status-ready">
                            Ready to claim in this league.
                          </span>
                        )
                    }
                  </div>
                </div>

                <div className="recent-drop-side">
                  <div className="recent-drop-value">
                    <span>{data.value_label}</span>
                    <strong>
                      {
                        formatSelectedValue(
                          player.selected_value,
                          valueBasis,
                        )
                      }
                    </strong>
                  </div>

                  <div className="recent-drop-time">
                    <Clock3 size={14} />
                    <span>{formatDroppedAt(player.dropped_at_ms)}</span>
                  </div>

                  <div className="recent-drop-actions">
                    <button
                      type="button"
                      className="button-secondary available-claim-button recent-drop-claim-button"
                      disabled={!!claimDisabledReason}
                      onClick={() => {
                        setClaimPlayer(player);
                      }}
                    >
                      Claim player
                    </button>
                  </div>
                </div>
              </article>
            );
          })
        }
      </div>

      {
        claimPlayer && modalLeague && modalPlayer
          ? (
            <AvailablePlayerClaimModal
              league={modalLeague}
              addPlayer={modalPlayer}
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
