import {
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  useEffect,
  useState,
} from 'react';

import { useRosterWaiverPlayers } from '@/hooks/sleeper/useWaivers';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';

import type {
  BulkWaiverLeagueAvailability,
  ValueBasis,
  WaiverClaimRequest,
} from '@/types';

import {
  formatSelectedValue,
} from './waiver.formatters';


interface BulkClaimLeagueRowProps {
  targetPlayerId?: string | null;
  targetPlayerName: string;

  league: BulkWaiverLeagueAvailability;
  valueBasis: ValueBasis;

  draftClaim: WaiverClaimRequest | undefined;
  canWrite: boolean;

  onToggle: (
    league: BulkWaiverLeagueAvailability,
  ) => void;

  onChange: (
    claim: WaiverClaimRequest,
  ) => void;
}


export const BulkClaimLeagueRow = ({
  targetPlayerId,
  targetPlayerName,
  league,
  valueBasis,
  draftClaim,
  canWrite,
  onToggle,
  onChange,
}: BulkClaimLeagueRowProps) => {
  const [showDropOptions, setShowDropOptions] = useState(false);

  const isSelected = draftClaim !== undefined;

  const rosterPlayers = useRosterWaiverPlayers(
    league.league_id,
    valueBasis,
    isSelected && showDropOptions,
  );

  const hasOpenRosterSpot = (
    league.roster_spots_available > 0
  );

  useEffect(() => {
    if (
      !isSelected
      || !draftClaim
      || !league.requires_drop
      || draftClaim.drop_player_id
    ) {
      return;
    }

    if (
      league.recommended_drop
    ) {
      onChange({
        ...draftClaim,
        drop_player_id: (
          league.recommended_drop.player_id
        ),
      });
    }
  }, [
    draftClaim,
    isSelected,
    league.recommended_drop,
    league.requires_drop,
    onChange,
  ]);

  const selectedDropPlayer = (
    rosterPlayers.data?.players.find(
      (player) => (
        player.player_id === draftClaim?.drop_player_id
      ),
    )
  );

  if (!league.is_available) {
    return (
      <article className="bulk-claim-league-row unavailable">
        <div className="bulk-league-main">
          <strong>
            {league.league_name}
          </strong>

          <span>
            {league.unavailable_reason ?? 'Unavailable'}
          </span>
        </div>

        <span className="bulk-unavailable-status">
          Unavailable
        </span>
      </article>
    );
  }

  if (!league.can_submit_claim) {
    return (
      <article className="bulk-claim-league-row blocked">
        <div className="bulk-league-main">
          <strong>
            {league.league_name}
          </strong>

          <span>
            {league.claim_blocked_reason}
          </span>
        </div>

        <div className="bulk-blocked-status">
          {league.roster_spots_available} spots
        </div>
      </article>
    );
  }

  return (
    <article
      className={
        `bulk-claim-league-row ${
          isSelected
            ? 'selected'
            : ''
        }`
      }
    >
      <div className="bulk-league-selection">
        <input
          type="checkbox"
          checked={isSelected}
          disabled={!canWrite}
          onChange={() => {
            onToggle(league);
          }}
          aria-label={
            `Select ${league.league_name} claim`
          }
        />

        <div className="bulk-league-main">
          <strong>
            {league.league_name}
          </strong>

          <span>
            ${league.faab_remaining} FAAB
            {' · '}
            {
              league.roster_spots_available > 0
                ? `${league.roster_spots_available} open spots`
                : 'Drop required'
            }
          </span>
        </div>
      </div>

      <div className="bulk-league-target-value">
        <span>Target Value</span>

        <strong>
          {
            formatSelectedValue(
              league.add_selected_value,
              valueBasis,
            )
          }
        </strong>
      </div>

      {
        isSelected
        && draftClaim
          ? (
            <div className="bulk-claim-controls">
              <label>
                <span>FAAB Bid</span>

                <input
                  type="number"
                  min="0"
                  max={league.faab_remaining}
                  value={draftClaim.bid}
                  onChange={(event) => {
                    const nextBid = Number(
                      event.target.value,
                    );

                    onChange({
                      ...draftClaim,
                      bid: Number.isNaN(nextBid)
                        ? 0
                        : Math.min(
                          Math.max(nextBid, 0),
                          league.faab_remaining,
                        ),
                    });
                  }}
                />
              </label>

              <div className="bulk-drop-control">
                <div className="bulk-drop-control-header">
                  <span>Drop Player</span>

                  <button
                    className="bulk-drop-toggle"
                    onClick={() => {
                      setShowDropOptions(
                        !showDropOptions,
                      );
                    }}
                  >
                    {
                      showDropOptions
                        ? <ChevronUp size={14} />
                        : <ChevronDown size={14} />
                    }

                    {
                      showDropOptions
                        ? 'Hide options'
                        : 'Change drop'
                    }
                  </button>
                </div>

                {
                  !showDropOptions
                    ? (
                      <strong>
                        {
                          league.requires_drop
                            ? (
                              league.recommended_drop?.name
                              ?? 'Select a drop'
                            )
                            : (
                              draftClaim.drop_player_id
                                ? (
                                  selectedDropPlayer?.name
                                  ?? 'Selected player'
                                )
                                : 'No drop needed'
                            )
                        }
                      </strong>
                    )
                    : (
                      <select
                        value={
                          draftClaim.drop_player_id ?? ''
                        }
                        onChange={(event) => {
                          onChange({
                            ...draftClaim,
                            drop_player_id: (
                              event.target.value || null
                            ),
                          });
                        }}
                        disabled={rosterPlayers.loading}
                      >
                        {
                          hasOpenRosterSpot
                            ? (
                              <option value="">
                                No drop — open roster spot
                              </option>
                            )
                            : (
                              <option value="" disabled>
                                Select a player to drop
                              </option>
                            )
                        }

                        {
                          rosterPlayers.data?.players.map(
                            (player) => (
                              <option
                                key={player.player_id}
                                value={player.player_id}
                              >
                                {player.name}
                                {' — '}
                                {player.position ?? '—'}
                                {' — '}
                                {
                                  formatSelectedValue(
                                    player.selected_value,
                                    valueBasis,
                                  )
                                }
                              </option>
                            ),
                          )
                        }
                      </select>
                    )
                }
              </div>

              <div className="bulk-claim-preview">
                <div className="player-with-avatar">
                  <PlayerAvatar
                    playerId={targetPlayerId}
                    name={targetPlayerName}
                    size="sm"
                  />

                  <span>
                    Add {targetPlayerName}
                  </span>
                </div>

                <span>
                  {' → '}
                </span>

                {
                  draftClaim.drop_player_id
                    ? (
                      <div className="player-with-avatar">
                        <PlayerAvatar
                          playerId={
                            selectedDropPlayer?.player_id
                            ?? league.recommended_drop?.player_id
                          }
                          name={
                            selectedDropPlayer?.name
                            ?? league.recommended_drop?.name
                            ?? 'Selected player'
                          }
                          size="sm"
                        />

                        <span>
                          {
                            selectedDropPlayer?.name
                            ?? league.recommended_drop?.name
                            ?? 'Selected player'
                          }
                        </span>
                      </div>
                    )
                    : 'Open roster spot'
                }
              </div>
            </div>
          )
          : null
      }
    </article>
  );
};
