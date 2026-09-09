import {
  AlertTriangle,
  Check,
  LoaderCircle,
  Trash2,
  X,
} from 'lucide-react';

import type {
  CommissionerCutdownActionResult,
  CommissionerCutdownPlayer,
} from '@/types';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { TeamBadge } from '@/components/players/TeamBadge';
import { getPositionColor } from '@/utils/positions';
import './CutdownReviewModal.css';

export interface CutdownRosterPreview {
  leagueId: string;
  leagueName: string;
  rosterId: number;
  ownerName: string;
  overLimitCount: number;
  drops: CommissionerCutdownPlayer[];
}

export interface CutdownReviewModalProps {
  previews: CutdownRosterPreview[];
  submitting: boolean;
  results: CommissionerCutdownActionResult[];
  error: Error | null;
  onClose: () => void;
  onConfirm: () => void;
}

export function CutdownReviewModal({
  previews,
  submitting,
  results,
  error,
  onClose,
  onConfirm,
}: CutdownReviewModalProps) {
  const hasResults = results.length > 0;
  const successfulCount = results.filter((r) => r.success).length;

  const totalDropsCount = previews.reduce(
    (sum, p) => sum + p.drops.length,
    0,
  );

  return (
    <div
      className="cutdown-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cutdown-modal-title"
    >
      <div className="cutdown-review-modal">
        <div className="cutdown-review-header">
          <div>
            <span className="cutdown-review-kicker">Commissioner Enforcement</span>
            <h2 id="cutdown-modal-title" className="cutdown-review-title">
              {hasResults ? 'Cutdown Results' : 'Review Forced Drops'}
            </h2>
            <p className="cutdown-review-subtitle">
              {hasResults
                ? `${successfulCount} of ${results.length} actions completed`
                : `Dropping ${totalDropsCount} player${totalDropsCount === 1 ? '' : 's'} across ${previews.length} roster${previews.length === 1 ? '' : 's'} based on lowest KeepTradeCut (KTC) value.`}
            </p>
          </div>
          <button
            type="button"
            className="cutdown-modal-close"
            onClick={onClose}
            disabled={submitting}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {hasResults ? (
          <div className="cutdown-results-container">
            {results.map((result) => (
              <div
                key={`${result.league_id}-${result.roster_id ?? 'unknown'}`}
                className={`cutdown-result-row ${result.success ? 'success' : 'error'}`}
              >
                {result.success ? <Check size={16} /> : <X size={16} />}
                <div className="cutdown-result-text">
                  <strong>
                    {result.roster_id ? `Roster ${result.roster_id}` : 'League'}
                  </strong>
                  <span>
                    {result.success
                      ? (result.details || 'Drops executed successfully')
                      : (result.error || 'Failed to drop players')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="cutdown-preview-list">
            {previews.map((item) => (
              <div
                key={`${item.leagueId}-${item.rosterId}`}
                className="cutdown-preview-card"
              >
                <div className="cutdown-preview-card-header">
                  <div className="cutdown-preview-card-title-group">
                    <strong className="cutdown-preview-owner">{item.ownerName}</strong>
                    <span className="cutdown-preview-league">{item.leagueName}</span>
                  </div>
                  <span className="cutdown-preview-badge">
                    {item.overLimitCount} over limit · {item.drops.length} to drop
                  </span>
                </div>

                <div className="cutdown-drops-list">
                  {item.drops.length === 0 ? (
                    <div className="cutdown-no-drops-msg">
                      No eligible players identified to drop.
                    </div>
                  ) : (
                    item.drops.map((player) => (
                      <div key={player.player_id} className="cutdown-player-row">
                        <div className="cutdown-player-info">
                          <PlayerAvatar
                            playerId={player.player_id}
                            name={player.name}
                            size="sm"
                          />
                          <div className="cutdown-player-copy">
                            <span className="cutdown-player-name">{player.name}</span>
                            <div className="cutdown-player-meta">
                              {player.position && (
                                <span
                                  className="cutdown-position-tag"
                                  style={{ color: getPositionColor(player.position) }}
                                >
                                  {player.position}
                                </span>
                              )}
                              {player.team && (
                                <>
                                  <span>·</span>
                                  <TeamBadge team={player.team} size="xs" />
                                </>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="cutdown-player-value">
                          <span className="cutdown-ktc-label">KTC Value</span>
                          <strong className="cutdown-ktc-value">
                            {player.ktc_value != null ? player.ktc_value.toLocaleString() : '0'}
                          </strong>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {error && !hasResults && (
          <div className="cutdown-error-banner">
            <AlertTriangle size={15} />
            <span>{error.message || 'Failed to execute drops'}</span>
          </div>
        )}

        <div className="cutdown-modal-footer">
          {hasResults ? (
            <button
              type="button"
              className="button-primary"
              onClick={onClose}
            >
              Done
            </button>
          ) : (
            <>
              <button
                type="button"
                className="button-secondary"
                onClick={onClose}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="button-primary cutdown-confirm-btn"
                onClick={onConfirm}
                disabled={submitting || previews.length === 0 || totalDropsCount === 0}
              >
                {submitting ? (
                  <>
                    <LoaderCircle size={15} className="animate-spin" />
                    Dropping Players...
                  </>
                ) : (
                  <>
                    <Trash2 size={15} />
                    Confirm Force Drop ({totalDropsCount})
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
