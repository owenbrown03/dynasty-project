import {
  Check,
  LoaderCircle,
  Send,
  X,
} from 'lucide-react';
import {
  useEffect,
  useState,
} from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { LeagueAvatar } from '@/components/leagues/LeagueAvatar';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import {
  useRosterWaiverPlayers,
  useSubmitWaiverClaim,
} from '@/hooks/sleeper/useWaivers';
import type {
  ValueBasis,
  WaiverAvailablePlayer,
  WaiverLeagueOption,
} from '@/types';

import {
  formatSelectedValue,
} from './waiver.formatters';


interface AvailablePlayerClaimModalProps {
  league: WaiverLeagueOption;
  addPlayer: WaiverAvailablePlayer;
  valueBasis: ValueBasis;
  onClose: () => void;
}


export const AvailablePlayerClaimModal = ({
  league,
  addPlayer,
  valueBasis,
  onClose,
}: AvailablePlayerClaimModalProps) => {
  const [dropPlayerId, setDropPlayerId] = useState('');
  const [bid, setBid] = useState(0);

  const rosterPlayers = useRosterWaiverPlayers(
    league.league_id,
    valueBasis,
    true,
  );

  const claim = useSubmitWaiverClaim();

  const hasOpenRosterSpot = (
    league.roster_spots_available > 0
  );

  useEffect(() => {
    if (
      !hasOpenRosterSpot
      && rosterPlayers.data
      && rosterPlayers.data.players.length > 0
      && !dropPlayerId
    ) {
      setDropPlayerId(
        rosterPlayers.data.players[0].player_id,
      );
    }
  }, [
    dropPlayerId,
    hasOpenRosterSpot,
    rosterPlayers.data,
  ]);

  const selectedDropPlayer = (
    rosterPlayers.data?.players.find(
      (player) => (
        player.player_id === dropPlayerId
      ),
    )
  );

  const handleSubmit = () => {
    if (
      claim.submitting
      || (
        !hasOpenRosterSpot
        && !dropPlayerId
      )
    ) {
      return;
    }

    claim.submitClaim({
      league_id: league.league_id,
      roster_id: league.roster_id,

      add_player_id: addPlayer.player_id,

      drop_player_id: (
        dropPlayerId || null
      ),

      bid,
    });
  };

  return (
    <div
      className="waiver-claim-modal-backdrop"
      onMouseDown={onClose}
    >
      <div
        className="waiver-claim-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="available-claim-title"
        onMouseDown={(event) => {
          event.stopPropagation();
        }}
      >
        <div className="waiver-claim-modal-header">
          <div className="waiver-claim-league-identity">
            <LeagueAvatar
              avatarId={league.league_avatar}
              name={league.league_name}
              size="md"
            />

            <div>
              <p>
                {league.league_name}
              </p>

              <h2 id="available-claim-title">
                Build Waiver Claim
              </h2>
            </div>
          </div>

          <button
            className="waiver-modal-close-button"
            onClick={onClose}
            disabled={claim.submitting}
            aria-label="Close claim form"
          >
            <X size={18} />
          </button>
        </div>

        {
          claim.success
            ? (
              <div className="waiver-modal-success">
                <Check size={18} />

                <div>
                  <strong>Claim submitted</strong>

                  <span>
                    Sleeper transaction created successfully.
                  </span>
                </div>
              </div>
            )
            : (
              <>
                <div className="waiver-modal-player-summary">
                  <div>
                    <span>Add</span>

                    <div className="player-with-avatar">
                      <PlayerAvatar
                        playerId={addPlayer.player_id}
                        name={addPlayer.name}
                        size="sm"
                      />

                      <strong>
                        {addPlayer.name}
                      </strong>
                    </div>

                    <small>
                      {addPlayer.position ?? '—'}
                      {' · '}
                      {addPlayer.team ?? 'FA'}
                      {' · '}
                      {
                        formatSelectedValue(
                          addPlayer.selected_value,
                          valueBasis,
                        )
                      }
                    </small>
                  </div>

                  <div>
                    <span>Drop</span>

                    {
                      selectedDropPlayer
                        ? (
                          <div className="player-with-avatar">
                            <PlayerAvatar
                              playerId={selectedDropPlayer.player_id}
                              name={selectedDropPlayer.name}
                              size="sm"
                            />

                            <strong>
                              {selectedDropPlayer.name}
                            </strong>
                          </div>
                        )
                        : (
                          <strong>
                            {
                              hasOpenRosterSpot
                                ? 'No drop needed'
                                : 'Choose a player'
                            }
                          </strong>
                        )
                    }

                    {
                      selectedDropPlayer
                        ? (
                          <small>
                            {
                              formatSelectedValue(
                                selectedDropPlayer.selected_value,
                                valueBasis,
                              )
                            }
                          </small>
                        )
                        : null
                    }
                  </div>
                </div>

                <label className="waiver-modal-field">
                  <span>Drop Player</span>

                  <select
                    value={dropPlayerId}
                    onChange={(event) => {
                      setDropPlayerId(
                        event.target.value,
                      );
                    }}
                    disabled={
                      rosterPlayers.loading
                      || claim.submitting
                    }
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
                </label>

                <label className="waiver-modal-field">
                  <span>
                    FAAB Bid
                    {' '}
                    <small>
                      (${league.faab_remaining} remaining)
                    </small>
                  </span>

                  <input
                    type="number"
                    min="0"
                    max={league.faab_remaining}
                    step="1"
                    value={bid}
                    onChange={(event) => {
                      const nextBid = Number(
                        event.target.value,
                      );

                      setBid(
                        Number.isNaN(nextBid)
                          ? 0
                          : Math.min(
                            Math.max(nextBid, 0),
                            league.faab_remaining,
                          ),
                      );
                    }}
                    disabled={claim.submitting}
                  />
                </label>

                {
                  rosterPlayers.loading
                    ? (
                      <LoadingState
                        label="Loading your roster players..."
                        inline
                        className="waiver-modal-loading"
                      />
                    )
                    : null
                }

                {
                  rosterPlayers.error
                    ? (
                      <p className="waiver-modal-error">
                        Unable to load roster players.
                      </p>
                    )
                    : null
                }

                {
                  claim.error
                    ? (
                      <p className="waiver-modal-error">
                        {claim.error.message}
                      </p>
                    )
                    : null
                }

                <div className="waiver-modal-actions">
                  <button
                    className="button-secondary"
                    onClick={onClose}
                    disabled={claim.submitting}
                  >
                    Cancel
                  </button>

                  <button
                    className="button-secondary waiver-modal-submit-button"
                    onClick={handleSubmit}
                    disabled={
                      claim.submitting
                      || rosterPlayers.loading
                      || (
                        !hasOpenRosterSpot
                        && !dropPlayerId
                      )
                    }
                  >
                    {
                      claim.submitting
                        ? (
                          <LoaderCircle
                            className="waiver-spinner"
                            size={14}
                          />
                        )
                        : (
                          <Send size={14} />
                        )
                    }

                    {
                      claim.submitting
                        ? 'Submitting...'
                        : `Submit $${bid} Claim`
                    }
                  </button>
                </div>
              </>
            )
        }
      </div>
    </div>
  );
};
