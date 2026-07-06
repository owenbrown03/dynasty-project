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

import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useSubmitWaiverClaim } from '@/hooks/sleeper/useWaivers';

import type {
  PlayerValue,
  WaiverLeagueOverview,
} from '@/types';


interface WaiverClaimActionProps {
  league: WaiverLeagueOverview;

  disabled?: boolean;
  disabledReason?: string;
}


function getErrorMessage(
  error: Error | null,
): string {
  if (!error) {
    return 'Unable to submit the waiver claim.';
  }

  return error.message;
}


export const WaiverClaimAction = ({
  league,
  disabled = false,
  disabledReason,
}: WaiverClaimActionProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [bid, setBid] = useState(0);

  const {
    canWrite,
  } = useSleeperConnection();

  const {
    submitClaim,
    submitting,
    success,
    error,
    reset,
  } = useSubmitWaiverClaim();

  const addPlayer: PlayerValue | null = (
    league.suggested_add
  );

  const dropPlayer: PlayerValue | null = (
    league.suggested_drop
  );

  const canBuildClaim = (
    canWrite
    && league.can_submit_claim
    && !disabled
    && addPlayer !== null
    && dropPlayer !== null
  );

  useEffect(() => {
    if (!isOpen) {
      reset();
    }
  }, [
    isOpen,
    reset,
  ]);

  useEffect(() => {
    if (disabled && isOpen) {
      setIsOpen(false);
    }
  }, [
    disabled,
    isOpen,
  ]);

  const handleOpen = () => {
    if (!canBuildClaim) {
      return;
    }

    setBid(0);
    setIsOpen(true);
  };

  const handleSubmit = () => {
    if (
      !canBuildClaim
      || !addPlayer
      || !dropPlayer
      || submitting
    ) {
      return;
    }

    submitClaim({
      league_id: league.league_id,
      roster_id: league.roster_id,

      add_player_id: addPlayer.player_id,
      drop_player_id: dropPlayer.player_id,

      bid,
    });
  };

  if (!canWrite) {
    return (
      <span className="waiver-read-only">
        Enable write access to submit claims
      </span>
    );
  }

  if (disabled) {
    return (
      <span
        className="waiver-read-only waiver-claim-blocked"
        title={disabledReason}
      >
        {disabledReason ?? 'Waiver claims are unavailable'}
      </span>
    );
  }

  if (!league.can_submit_claim) {
    return (
      <span className="waiver-read-only">
        This league is not currently eligible for a waiver claim
      </span>
    );
  }

  if (!canBuildClaim) {
    return (
      <span className="waiver-read-only">
        A valid add and drop are required
      </span>
    );
  }

  if (!isOpen) {
    return (
      <button
        className="button-secondary waiver-claim-button"
        onClick={handleOpen}
      >
        <Send size={14} />
        Build Claim
      </button>
    );
  }

  if (success) {
    return (
      <div className="waiver-claim-success">
        <Check size={14} />
        Claim submitted
      </div>
    );
  }

  return (
    <div className="waiver-claim-form">
      <div className="waiver-claim-summary">
        <span>
          Add <strong>{addPlayer.name}</strong>
        </span>

        <span>
          Drop <strong>{dropPlayer.name}</strong>
        </span>
      </div>

      <label className="waiver-bid-input">
        <span>
          FAAB Bid
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

            if (Number.isNaN(nextBid)) {
              setBid(0);
              return;
            }

            setBid(
              Math.min(
                Math.max(nextBid, 0),
                league.faab_remaining,
              ),
            );
          }}
          disabled={submitting}
        />
      </label>

      <div className="waiver-claim-actions">
        <button
          className="button-secondary waiver-cancel-claim-button"
          onClick={() => {
            setIsOpen(false);
          }}
          disabled={submitting}
        >
          <X size={14} />
          Cancel
        </button>

        <button
          className="button-secondary waiver-submit-claim-button"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {
            submitting
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
            submitting
              ? 'Submitting...'
              : `Submit $${bid} Claim`
          }
        </button>
      </div>

      {
        error
          ? (
            <p className="waiver-claim-error">
              {getErrorMessage(error)}
            </p>
          )
          : null
      }
    </div>
  );
};