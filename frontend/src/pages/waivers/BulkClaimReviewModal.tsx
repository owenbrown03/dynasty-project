import {
  Check,
  LoaderCircle,
  Send,
  X,
} from 'lucide-react';

import type {
  BulkWaiverPlayerSearchResult,
  BulkWaiverClaimResponse,
  WaiverClaimRequest,
} from '@/types';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';


interface BulkClaimReviewModalProps {
  player: BulkWaiverPlayerSearchResult;

  claims: WaiverClaimRequest[];
  leagueNamesById: Record<string, string>;

  submitting: boolean;
  result: BulkWaiverClaimResponse | undefined;
  error: Error | null;

  onClose: () => void;
  onSubmit: () => void;
}


export const BulkClaimReviewModal = ({
  player,
  claims,
  leagueNamesById,
  submitting,
  result,
  error,
  onClose,
  onSubmit,
}: BulkClaimReviewModalProps) => {
  const successCount = (
    result?.results.filter(
      (item) => item.success,
    ).length
    ?? 0
  );

  if (result) {
    return (
      <div
        className="bulk-review-backdrop"
        onMouseDown={onClose}
      >
        <div
          className="bulk-review-modal"
          onMouseDown={(event) => {
            event.stopPropagation();
          }}
        >
          <div className="bulk-review-header">
            <div>
              <p>Bulk Claim Results</p>

              <h2>
                {successCount}
                /
                {result.results.length}
                {' '}claims submitted
              </h2>
            </div>

            <button
              className="waiver-modal-close-button"
              onClick={onClose}
            >
              <X size={18} />
            </button>
          </div>

          <div className="bulk-result-list">
            {
              result.results.map((item) => (
                <div
                  key={item.league_id}
                  className={
                    `bulk-result-row ${
                      item.success
                        ? 'success'
                        : 'error'
                    }`
                  }
                >
                  <div>
                    <strong>
                      {
                        leagueNamesById[
                          item.league_id
                        ]
                        ?? item.league_id
                      }
                    </strong>

                    <span>
                      {
                        item.success
                          ? 'Claim submitted'
                          : (
                            item.error
                            ?? 'Claim failed'
                          )
                      }
                    </span>
                  </div>

                  {
                    item.success
                      ? <Check size={17} />
                      : null
                  }
                </div>
              ))
            }
          </div>

          <div className="bulk-review-actions">
            <button
              className="button-secondary"
              onClick={onClose}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="bulk-review-backdrop"
      onMouseDown={() => {
        if (!submitting) {
          onClose();
        }
      }}
    >
      <div
        className="bulk-review-modal"
        onMouseDown={(event) => {
          event.stopPropagation();
        }}
      >
        <div className="bulk-review-header">
          <div>
            <p>Review Bulk Claims</p>

            <h2>
              Submit {claims.length} claim{
                claims.length === 1
                  ? ''
                  : 's'
              }?
            </h2>
          </div>

          <button
            className="waiver-modal-close-button"
            onClick={onClose}
            disabled={submitting}
          >
            <X size={18} />
          </button>
        </div>

        <div className="bulk-review-list">
          {
            claims.map((claim) => (
              <div
                key={claim.league_id}
                className="bulk-review-row"
              >
                <div>
                  <strong>
                    {
                      leagueNamesById[
                        claim.league_id
                      ]
                    }
                  </strong>

                  <span>
                    <span className="player-with-avatar">
                      <PlayerAvatar
                        playerId={player.player_id}
                        name={player.name}
                        size="sm"
                      />

                      <span>Add {player.name}</span>
                    </span>
                  </span>
                </div>

                <div>
                  <span>
                    {
                      claim.drop_player_id
                        ? 'Drop selected player'
                        : 'No drop needed'
                    }
                  </span>

                  <strong>
                    ${claim.bid}
                  </strong>
                </div>
              </div>
            ))
          }
        </div>

        {
          error
            ? (
              <p className="waiver-modal-error">
                {error.message}
              </p>
            )
            : null
        }

        <div className="bulk-review-actions">
          <button
            className="button-secondary"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </button>

          <button
            className="button-secondary waiver-modal-submit-button"
            onClick={onSubmit}
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
                : `Submit ${claims.length} Claims`
            }
          </button>
        </div>
      </div>
    </div>
  );
};
