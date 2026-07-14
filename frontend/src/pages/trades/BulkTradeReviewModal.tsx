import {
  Check,
  LoaderCircle,
  Send,
  X,
} from 'lucide-react';

import type {
  BulkTradeOfferRequest,
  BulkTradeProposalResult,
  BulkTradePlayerSearchResult,
  TradeDirection,
} from '@/types';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';


interface ReviewOffer {
  offer: BulkTradeOfferRequest;
  leagueName: string;
  counterpartyName: string;
  pickLabels: string[];
}


interface BulkTradeReviewModalProps {
  direction: TradeDirection;
  players: BulkTradePlayerSearchResult[];
  offers: ReviewOffer[];

  submitting: boolean;
  results: BulkTradeProposalResult[];

  error: Error | null;

  onClose: () => void;
  onSubmit: () => void;
}


function getErrorMessage(
  error: Error | null,
): string | null {
  if (!error) {
    return null;
  }

  return error.message;
}


export const BulkTradeReviewModal = ({
  direction,
  players,
  offers,
  submitting,
  results,
  error,
  onClose,
  onSubmit,
}: BulkTradeReviewModalProps) => {
  const hasResults = results.length > 0;

  const successfulCount = results.filter(
    result => result.success,
  ).length;

  return (
    <div className="bulk-trade-modal-backdrop">
      <div className="bulk-trade-review-modal">
        <div className="bulk-trade-review-header">
          <div>
            <span>
              Review bulk offers
            </span>

            <div className="bulk-trade-player-heading">
              <PlayerAvatar
                playerId={players[0]?.player_id ?? 'unknown'}
                name={players[0]?.name ?? 'Players'}
                size="md"
              />

              <h2>
                {
                  direction === 'buy'
                    ? `Buy ${players.map(player => player.name).join(', ')}`
                    : `Sell ${players.map(player => player.name).join(', ')}`
                }
              </h2>
            </div>
          </div>

          <button
            className="bulk-trade-modal-close"
            onClick={onClose}
            disabled={submitting}
          >
            <X size={18} />
          </button>
        </div>

        {
          hasResults
            ? (
              <div className="bulk-trade-results-summary">
                <strong>
                  {successfulCount}
                  /
                  {results.length}
                  {' '}
                  offers submitted
                </strong>

                {
                  results.map(result => (
                    <div
                      key={result.league_id}
                      className={
                        `bulk-trade-result ${
                          result.success
                            ? 'success'
                            : 'error'
                        }`
                      }
                    >
                      {
                        result.success
                          ? <Check size={15} />
                          : <X size={15} />
                      }

                      <span>
                        {result.success
                          ? 'Trade offer submitted'
                          : result.error
                        }
                      </span>
                    </div>
                  ))
                }
              </div>
            )
            : (
              <div className="bulk-trade-review-list">
                {
                  offers.map(item => (
                    <article
                      key={item.offer.league_id}
                      className="bulk-trade-review-row"
                    >
                      <strong>
                        {item.leagueName}
                      </strong>

                      <span>
                        To: {item.counterpartyName}
                      </span>

                      <div>
                        {
                          direction === 'buy'
                            ? (
                              <>
                                <span>
                                  You send:
                                </span>

                                <strong>
                                  {item.pickLabels.join(', ')}
                                </strong>

                                <span>
                                  You receive:
                                </span>

                                <strong>
                                  {players.map(player => player.name).join(', ')}
                                </strong>
                              </>
                            )
                            : (
                              <>
                                <span>
                                  You send:
                                </span>

                                <strong>
                                  {players.map(player => player.name).join(', ')}
                                </strong>

                                <span>
                                  You receive:
                                </span>

                                <strong>
                                  {item.pickLabels.join(', ')}
                                </strong>
                              </>
                            )
                        }
                      </div>
                    </article>
                  ))
                }
              </div>
            )
        }

        {
          getErrorMessage(error)
            ? (
              <p className="bulk-trade-submit-error">
                {getErrorMessage(error)}
              </p>
            )
            : null
        }

        <div className="bulk-trade-review-actions">
          <button
            className="button-secondary"
            onClick={onClose}
            disabled={submitting}
          >
            {
              hasResults
                ? 'Close'
                : 'Cancel'
            }
          </button>

          {
            !hasResults
              ? (
                <button
                  className="button-secondary bulk-trade-submit-button"
                  onClick={onSubmit}
                  disabled={
                    submitting
                    || offers.length === 0
                  }
                >
                  {
                    submitting
                      ? (
                        <LoaderCircle
                          className="trade-spinner"
                          size={15}
                        />
                      )
                      : (
                        <Send size={15} />
                      )
                  }

                  {
                    submitting
                      ? 'Sending offers...'
                      : `Send ${offers.length} Trade ${
                        offers.length === 1
                          ? 'Offer'
                          : 'Offers'
                      }`
                  }
                </button>
              )
              : null
          }
        </div>
      </div>
    </div>
  );
};
