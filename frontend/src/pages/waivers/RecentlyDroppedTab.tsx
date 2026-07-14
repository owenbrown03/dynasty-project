import { useMemo, useState } from 'react';
import {
  AlertTriangle,
  Clock3,
  HandCoins,
} from 'lucide-react';

import { LoadingState } from '@/components/feedback/LoadingState';
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


export const RecentlyDroppedTab = ({
  valueBasis,
}: RecentlyDroppedTabProps) => {
  const [claimPlayer, setClaimPlayer] = useState<WaiverRecentlyDroppedPlayer | null>(
    null,
  );
  const recentDrops = useRecentlyDroppedPlayers(
    valueBasis,
  );
  const {
    canWrite,
  } = useSleeperConnection();

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
      };
    },
    [claimPlayer],
  );

  if (recentDrops.loading) {
    return (
      <LoadingState
        label="Loading recently dropped players..."
        className="waivers-loading-state"
      />
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
            Ranked by {data.value_label}
          </span>
        </div>
      </div>

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
                </div>

                <div className="recent-drop-meta-row">
                  <div className="recent-drop-league">
                    <LeagueAvatar
                      avatarId={player.league_avatar}
                      name={player.league_name}
                      size="sm"
                    />

                    <div>
                      <strong>{player.league_name}</strong>
                      <span>
                        FAAB ${player.faab_remaining}
                        {' · '}
                        {player.faab_percent_remaining.toFixed(1)}% left
                      </span>
                    </div>
                  </div>

                  <div className="recent-drop-time">
                    <Clock3 size={14} />
                    <span>{formatDroppedAt(player.dropped_at_ms)}</span>
                  </div>
                </div>

                <div className="recent-drop-footer">
                  {
                    claimDisabledReason
                      ? (
                        <span className="waiver-read-only">
                          {claimDisabledReason}
                        </span>
                      )
                      : (
                        <span className="waiver-read-only">
                          Ready to claim in this league.
                        </span>
                      )
                  }

                  <button
                    type="button"
                    className="button-secondary waiver-claim-button"
                    disabled={!!claimDisabledReason}
                    onClick={() => {
                      setClaimPlayer(player);
                    }}
                  >
                    Claim player
                  </button>
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
