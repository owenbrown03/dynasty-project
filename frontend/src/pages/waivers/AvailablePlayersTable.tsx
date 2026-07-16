import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Send,
} from 'lucide-react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type {
  ValueBasis,
  WaiverAvailableLeagueAvailability,
  WaiverAvailablePlayer,
  WaiverAvailablePlayersResponse,
} from '@/types';

import {
  formatAge,
  formatMarketValue,
  formatSelectedValue,
  formatWar,
} from './waiver.formatters';


interface AvailablePlayersTableProps {
  data: WaiverAvailablePlayersResponse;
  canWrite: boolean;

  onClaim: (
    player: WaiverAvailablePlayer,
  ) => void;
}


interface AvailablePlayersRowProps {
  player: WaiverAvailablePlayer;
  valueBasis: ValueBasis;
  valueLabel: string;
  isAllLeagues: boolean;
  canWrite: boolean;
  expanded: boolean;
  onToggleExpanded: (
    playerId: string,
  ) => void;
  onClaim: (
    player: WaiverAvailablePlayer,
  ) => void;
}


function buildClaimPlayer(
  player: WaiverAvailablePlayer,
  availability: WaiverAvailableLeagueAvailability,
): WaiverAvailablePlayer {
  return {
    ...player,
    league_id: availability.league_id,
    league_name: availability.league_name,
    league_avatar: availability.league_avatar,
    roster_id: availability.roster_id,
    roster_size: availability.roster_size,
    roster_capacity:
      availability.roster_capacity,
    roster_spots_available:
      availability.roster_spots_available,
    faab_remaining:
      availability.faab_remaining,
    faab_percent_remaining:
      availability.faab_percent_remaining,
    can_submit_claim:
      availability.can_submit_claim,
    claim_blocked_reason:
      availability.claim_blocked_reason,
    selected_value:
      availability.selected_value,
  };
}


const AvailablePlayersRow = ({
  player,
  valueBasis,
  valueLabel,
  isAllLeagues,
  canWrite,
  expanded,
  onToggleExpanded,
  onClaim,
}: AvailablePlayersRowProps) => {
  const rowCanClaim = (
    canWrite
    && player.can_submit_claim
  );
  const claimTitle = player.claim_blocked_reason
    ?? (
      canWrite
        ? 'Build a waiver claim'
        : 'Enable Sleeper write access to submit claims'
    );
  const primaryLeague = (
    player.league_availability[0]
  );

  return (
    <>
      <tr>
        <td className="available-player-name-cell">
          <div className="player-with-avatar">
            <PlayerAvatar
              playerId={player.player_id}
              name={player.name}
              size="sm"
            />

            <div className="player-with-avatar-copy">
              <strong>
                {player.name}
              </strong>

              <span>
                {player.underdog_position_rank ?? '—'}
              </span>
            </div>
          </div>
        </td>

        <td>
          {player.position ?? '—'}
        </td>

        <td>
          {player.team ?? 'FA'}
        </td>

        {
          isAllLeagues
            ? (
              <td className="available-league-cell">
                <strong>
                  {player.league_count} leagues
                </strong>

                <span>
                  Best fit:{' '}
                  {
                    primaryLeague?.league_name
                    ?? '—'
                  }
                </span>
              </td>
            )
            : null
        }

        <td>
          {formatAge(player.age)}
        </td>

        <td className="available-selected-value">
          <strong>
            {
              formatSelectedValue(
                player.selected_value,
                valueBasis,
              )
            }
          </strong>

          <span>
            {valueLabel}
          </span>
        </td>

        <td>
          {formatMarketValue(player.ktc_value)}
        </td>

        <td>
          {formatMarketValue(player.fc_value)}
        </td>

        <td>
          {formatWar(player.dynasty_roster_war)}
        </td>

        <td>
          {formatWar(player.redraft_roster_war)}
        </td>

        <td>
          {
            isAllLeagues
              ? (
                <button
                  type="button"
                  className="button-secondary available-claim-button"
                  onClick={() => {
                    onToggleExpanded(
                      player.player_id,
                    );
                  }}
                >
                  {
                    expanded
                      ? <ChevronUp size={13} />
                      : <ChevronDown size={13} />
                  }
                  {
                    expanded
                      ? 'Hide leagues'
                      : 'View leagues'
                  }
                </button>
              )
              : (
                <button
                  className="button-secondary available-claim-button"
                  onClick={() => {
                    onClaim(player);
                  }}
                  disabled={!rowCanClaim}
                  title={claimTitle}
                >
                  <Send size={13} />
                  Claim
                </button>
              )
          }
        </td>
      </tr>

      {
        isAllLeagues
        && expanded
          ? (
            <tr className="available-player-detail-row">
              <td
                colSpan={11}
                className="available-player-detail-cell"
              >
                <div className="available-player-detail-list">
                  {
                    player.league_availability.map(
                      (availability) => {
                        const detailCanClaim = (
                          canWrite
                          && availability.can_submit_claim
                        );
                        const detailClaimTitle = (
                          availability.claim_blocked_reason
                          ?? (
                            canWrite
                              ? 'Build a waiver claim'
                              : 'Enable Sleeper write access to submit claims'
                          )
                        );

                        return (
                          <div
                            key={`${availability.league_id}:${player.player_id}`}
                            className="available-player-detail-card"
                          >
                            <div className="available-player-detail-copy">
                              <strong>
                                {availability.league_name}
                              </strong>

                              <span>
                                {
                                  formatSelectedValue(
                                    availability.selected_value,
                                    valueBasis,
                                  )
                                }
                                {' · '}
                                FAAB $
                                {
                                  availability.faab_remaining
                                }
                                {' · '}
                                Spots{' '}
                                {
                                  availability.roster_spots_available
                                }
                              </span>
                            </div>

                            <button
                              type="button"
                              className="button-secondary available-claim-button"
                              disabled={!detailCanClaim}
                              title={detailClaimTitle}
                              onClick={() => {
                                onClaim(
                                  buildClaimPlayer(
                                    player,
                                    availability,
                                  ),
                                );
                              }}
                            >
                              <Send size={13} />
                              Claim
                            </button>
                          </div>
                        );
                      },
                    )
                  }
                </div>
              </td>
            </tr>
          )
          : null
      }
    </>
  );
};


export const AvailablePlayersTable = ({
  data,
  canWrite,
  onClaim,
}: AvailablePlayersTableProps) => {
  const [
    expandedPlayerId,
    setExpandedPlayerId,
  ] = useState<string | null>(null);

  return (
    <div className="available-players-table-wrapper">
      <table className="available-players-table">
        <thead>
          <tr>
            <th>Player</th>
            <th>Pos</th>
            <th>Team</th>
            {
              data.is_all_leagues
                ? <th>Leagues</th>
                : null
            }
            <th>Age</th>
            <th>{data.value_label}</th>
            <th>KTC</th>
            <th>FC</th>
            <th>Dynasty WAR</th>
            <th>Redraft WAR</th>
            <th />
          </tr>
        </thead>

        <tbody>
          {
            data.players.map((player) => (
              <AvailablePlayersRow
                key={player.player_id}
                player={player}
                valueBasis={data.value_basis}
                valueLabel={data.value_label}
                isAllLeagues={
                  data.is_all_leagues
                }
                canWrite={canWrite}
                expanded={
                  expandedPlayerId
                  === player.player_id
                }
                onToggleExpanded={(
                  playerId,
                ) => {
                  setExpandedPlayerId(
                    expandedPlayerId === playerId
                      ? null
                      : playerId,
                  );
                }}
                onClaim={onClaim}
              />
            ))
          }
        </tbody>
      </table>
    </div>
  );
};
