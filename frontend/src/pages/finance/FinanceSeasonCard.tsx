import type {
  FinanceLeagueSeasonEntry,
} from '@/types';
import { formatNumber } from '@/utils/format';
import {
  financeResultLabel,
  formatCurrency,
  projectionSourceLabel,
  sourceLabel,
  type FinanceSeasonDraft,
} from './finance.utils';
import { FinancePayoutEditor } from './FinancePayoutEditor';

interface FinanceSeasonCardProps {
  entry: FinanceLeagueSeasonEntry;
  draft: FinanceSeasonDraft;
  onDraftChange: (
    nextDraft: FinanceSeasonDraft,
  ) => void;
  onReset: () => void;
  resetPending: boolean;
}

export function FinanceSeasonCard({
  entry,
  draft,
  onDraftChange,
  onReset,
  resetPending,
}: FinanceSeasonCardProps) {
  return (
    <article className="finance-card">
      <header className="finance-card-header">
        <div>
          <p className="finance-card-kicker">{entry.season}</p>
          <h2 className="finance-card-title">
            {entry.league_name}
          </h2>
          <p className="finance-card-subtitle">
            {financeResultLabel(entry)}
            {
              entry.points_for !== null
                ? ` · PF ${formatNumber(entry.points_for)}`
                : ''
            }
          </p>
        </div>

        <div className="finance-card-net">
          <span>Net</span>
          <strong>{formatCurrency(entry.net_amount)}</strong>
        </div>
      </header>

      <div className="finance-card-grid">
        <div>
          <span>Buy-in</span>
          <strong>{formatCurrency(entry.buy_in_amount)}</strong>
          <small>{sourceLabel(entry.buy_in_source)}</small>
        </div>
        <div>
          <span>Finish payout</span>
          <strong>{formatCurrency(entry.winnings_amount)}</strong>
          <small>{sourceLabel(entry.payout_source)}</small>
        </div>
        <div>
          <span>Expected payout</span>
          <strong>{formatCurrency(entry.projected_winnings_amount)}</strong>
          <small>
            {projectionSourceLabel(entry.projected_winnings_source)}
          </small>
        </div>
      </div>

      <div className="finance-inline-flags">
        <label className="finance-inline-checkbox">
          <input
            type="checkbox"
            checked={draft.isExcluded}
            onChange={(event) => {
              onDraftChange({
                ...draft,
                isExcluded: event.target.checked,
              });
            }}
          />
          Exclude this season from totals and charts
        </label>

        {
          entry.has_season_override
            ? (
              <button
                type="button"
                className="button-secondary"
                disabled={resetPending}
                onClick={onReset}
              >
                {
                  resetPending
                    ? 'Resetting...'
                    : 'Reset to inherited defaults'
                }
              </button>
            )
            : null
        }
      </div>

      <div className="finance-form-grid">
        <label>
          <span>Season buy-in override</span>
          <input
            type="number"
            min="0"
            step="1"
            value={draft.buyInAmount}
            onChange={(event) => {
              onDraftChange({
                ...draft,
                buyInAmount: event.target.value,
              });
            }}
          />
        </label>
      </div>

      <FinancePayoutEditor
        draft={draft}
        onChange={(nextDraft) => {
          onDraftChange({
            ...draft,
            ...nextDraft,
          });
        }}
      />
    </article>
  );
}
