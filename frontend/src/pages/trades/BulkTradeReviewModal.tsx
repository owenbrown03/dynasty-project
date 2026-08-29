import {
  Check,
  LoaderCircle,
  Send,
  X,
} from 'lucide-react';
import { useState } from 'react';

import type {
  BulkTradeOfferRequest,
  BulkTradePlayerSearchResult,
  BulkTradeProposalResult,
} from '@/types';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';


const EXPIRY_OPTIONS: { label: string; value: number | null }[] = [
  { label: 'No timer', value: null },
  { label: '1 hour', value: 3_600 },
  { label: '6 hours', value: 21_600 },
  { label: '24 hours', value: 86_400 },
  { label: '2 days', value: 172_800 },
  { label: '3 days', value: 259_200 },
  { label: '7 days', value: 604_800 },
];


interface ReviewOffer {
  offer: BulkTradeOfferRequest;
  leagueName: string;
  counterpartyName: string;
  sendPickLabels: string[];
  receivePickLabels: string[];
}


interface BulkTradeReviewModalProps {
  sendPlayers: BulkTradePlayerSearchResult[];
  receivePlayers: BulkTradePlayerSearchResult[];
  offers: ReviewOffer[];

  submitting: boolean;
  results: BulkTradeProposalResult[];

  error: Error | null;

  onClose: () => void;
  onSubmit: (expiresInSecs: number | null, sendDm: boolean) => void;
}


function getErrorMessage(
  error: Error | null,
): string | null {
  if (!error) {
    return null;
  }

  return error.message;
}


function renderAssetSummary(
  playerNames: string[],
  pickLabels: string[],
): string {
  return [
    ...playerNames,
    ...pickLabels,
  ].join(', ');
}


export const BulkTradeReviewModal = ({
  sendPlayers,
  receivePlayers,
  offers,
  submitting,
  results,
  error,
  onClose,
  onSubmit,
}: BulkTradeReviewModalProps) => {
  const [expiresInSecs, setExpiresInSecs] = useState<number | null>(172_800);
  const [sendDm, setSendDm] = useState(true);

  const hasResults = results.length > 0;

  const successfulCount = results.filter(
    result => result.success,
  ).length;

  const counterpartyNameById = new Map<number, string>();
  offers.forEach(item => {
    if (item.offer.counterparty_roster_id != null) {
      counterpartyNameById.set(
        item.offer.counterparty_roster_id,
        item.counterpartyName,
      );
    }
  });

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
                playerId={receivePlayers[0]?.player_id ?? sendPlayers[0]?.player_id ?? 'unknown'}
                name={receivePlayers[0]?.name ?? sendPlayers[0]?.name ?? 'Trade package'}
                size="md"
              />

              <h2>
                Mixed bulk trade package
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
                      key={
                        `${result.league_id}-${
                          result.counterparty_roster_id ?? 'unknown'
                        }`
                      }
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

                      <div className="bulk-trade-result-copy">
                        <span>
                          {result.success
                            ? 'Trade offer submitted'
                            : result.error
                          }
                        </span>

                        {
                          result.counterparty_roster_id != null
                            && counterpartyNameById.has(
                              result.counterparty_roster_id,
                            )
                            ? (
                              <small>
                                with {
                                  counterpartyNameById.get(
                                    result.counterparty_roster_id,
                                  )
                                }
                              </small>
                            )
                            : null
                        }
                      </div>
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
                      key={
                        `${item.offer.league_id}-${
                          item.offer.counterparty_roster_id ?? 'unknown'
                        }`
                      }
                      className="bulk-trade-review-row"
                    >
                      <strong>
                        {item.leagueName}
                      </strong>

                      <span>
                        To: {item.counterpartyName}
                      </span>

                      <div>
                        <span>
                          You send:
                        </span>

                        <strong>
                          {
                            renderAssetSummary(
                              sendPlayers.map(player => player.name),
                              item.sendPickLabels,
                            )
                          }
                        </strong>

                        <span>
                          You receive:
                        </span>

                        <strong>
                          {
                            renderAssetSummary(
                              receivePlayers.map(player => player.name),
                              item.receivePickLabels,
                            )
                          }
                        </strong>
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

        {
          !hasResults
            ? (
              <div className="advisor-expiry bulk-trade-expiry">
                <span className="advisor-expiry-label">
                  Offer expires
                </span>

                <div className="advisor-expiry-options">
                  {EXPIRY_OPTIONS.map((option) => (
                    <button
                      key={option.label}
                      type="button"
                      className={`advisor-expiry-option ${
                        expiresInSecs === option.value
                          ? 'advisor-expiry-active'
                          : ''
                      }`}
                      onClick={() => setExpiresInSecs(option.value)}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
            )
            : null
        }

        {
          !hasResults
            ? (
              <label className="advisor-dm-toggle bulk-trade-dm-toggle">
                <input
                  type="checkbox"
                  checked={sendDm}
                  onChange={event => setSendDm(event.target.checked)}
                />
                <span>DM each manager this trade on Sleeper</span>
              </label>
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
                  onClick={() => onSubmit(expiresInSecs, sendDm)}
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
