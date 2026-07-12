import { useEffect, useMemo, useState } from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import {
  useFinanceSummary,
  useSaveFinanceSeason,
} from '@/hooks/sleeper/useUsers';
import type {
  FinanceLeagueSeasonEntry,
} from '@/types';
import { formatNumber } from '@/utils/format';
import { notify } from '@/utils/notify';

import './FinancePage.css';


type FinanceDraft = {
  buyInAmount: string;
  winningsAmount: string;
};


function formatCurrency(
  value: number,
) {
  return new Intl.NumberFormat(
    'en-US',
    {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    },
  ).format(value);
}


function buildDrafts(
  entries: FinanceLeagueSeasonEntry[],
) {
  return Object.fromEntries(
    entries.map((entry) => [
      `${entry.league_id}-${entry.season}`,
      {
        buyInAmount: entry.buy_in_amount.toString(),
        winningsAmount: entry.winnings_amount.toString(),
      },
    ]),
  ) as Record<string, FinanceDraft>;
}


function getDraftKey(
  entry: FinanceLeagueSeasonEntry,
) {
  return `${entry.league_id}-${entry.season}`;
}


function parseDraftAmount(
  value: string,
) {
  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed
    : 0;
}


function isDraftDirty(
  entry: FinanceLeagueSeasonEntry,
  draft: FinanceDraft | undefined,
) {
  if (!draft) {
    return false;
  }

  return (
    parseDraftAmount(draft.buyInAmount) !== entry.buy_in_amount
    || parseDraftAmount(draft.winningsAmount) !== entry.winnings_amount
  );
}


function buildLinePoints(
  values: number[],
  width: number,
  height: number,
) {
  if (values.length === 0) {
    return '';
  }

  const minValue = Math.min(...values, 0);
  const maxValue = Math.max(...values, 1);
  const range = maxValue - minValue || 1;

  return values.map((value, index) => {
    const x = values.length === 1
      ? width / 2
      : (index / (values.length - 1)) * width;
    const y = height - (
      ((value - minValue) / range) * height
    );

    return `${x},${y}`;
  }).join(' ');
}


function FinanceTrendChart({
  entries,
}: {
  entries: FinanceLeagueSeasonEntry[];
}) {
  const chartEntries = [...entries].sort(
    (left, right) => (
      Number(left.season) - Number(right.season)
    ),
  );
  const actualValues = chartEntries.map(
    (entry) => entry.winnings_amount,
  );
  const projectedValues = chartEntries.map(
    (entry) => entry.projected_winnings_amount,
  );
  const actualPoints = buildLinePoints(
    actualValues,
    320,
    140,
  );
  const projectedPoints = buildLinePoints(
    projectedValues,
    320,
    140,
  );

  return (
    <article className="finance-chart-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">
            Trend
          </p>
          <h2>Winnings history vs current projection</h2>
        </div>

        <div className="finance-chart-legend">
          <span className="finance-legend-item">
            <i className="finance-legend-line finance-legend-line-actual" />
            Won
          </span>
          <span className="finance-legend-item">
            <i className="finance-legend-line finance-legend-line-projected" />
            Projected
          </span>
        </div>
      </div>

      {
        chartEntries.length > 0
          ? (
            <div className="finance-line-chart">
              <svg viewBox="0 0 320 140" aria-hidden="true">
                <polyline
                  fill="none"
                  stroke="var(--finance-actual-color)"
                  strokeWidth="3"
                  points={actualPoints}
                />
                <polyline
                  fill="none"
                  stroke="var(--finance-projected-color)"
                  strokeWidth="3"
                  strokeDasharray="6 6"
                  points={projectedPoints}
                />
                {
                  chartEntries.map((entry, index) => {
                    const actualPoint = actualPoints.split(' ')[index];
                    const projectedPoint = projectedPoints.split(' ')[index];
                    const [actualX, actualY] = actualPoint.split(',').map(Number);
                    const [projectedX, projectedY] = projectedPoint.split(',').map(Number);

                    return (
                      <g key={`${entry.league_id}-${entry.season}`}>
                        <circle
                          cx={actualX}
                          cy={actualY}
                          r="4"
                          fill="var(--finance-actual-color)"
                        />
                        <circle
                          cx={projectedX}
                          cy={projectedY}
                          r="4"
                          fill="var(--finance-projected-color)"
                        />
                      </g>
                    );
                  })
                }
              </svg>

              <div className="finance-chart-label-row">
                {
                  chartEntries.map((entry) => (
                    <span key={`${entry.league_id}-${entry.season}`}>
                      {entry.season}
                    </span>
                  ))
                }
              </div>
            </div>
          )
          : null
      }
    </article>
  );
}


function FinanceNetChart({
  entries,
}: {
  entries: FinanceLeagueSeasonEntry[];
}) {
  const chartEntries = [...entries].sort(
    (left, right) => (
      Number(left.season) - Number(right.season)
    ),
  );
  const maxMagnitude = Math.max(
    ...chartEntries.map((entry) => Math.abs(entry.net_amount)),
    1,
  );

  return (
    <article className="finance-chart-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">
            Net
          </p>
          <h2>Season-by-season net results</h2>
        </div>
      </div>

      <div className="finance-bar-chart">
        {
          chartEntries.map((entry) => {
            const width = `${(Math.abs(entry.net_amount) / maxMagnitude) * 100}%`;

            return (
              <div
                key={`${entry.league_id}-${entry.season}`}
                className="finance-bar-row"
              >
                <div className="finance-bar-copy">
                  <strong>{entry.season}</strong>
                  <span>{entry.league_name}</span>
                </div>

                <div className="finance-bar-track">
                  <div
                    className={
                      entry.net_amount >= 0
                        ? 'finance-bar finance-bar-positive'
                        : 'finance-bar finance-bar-negative'
                    }
                    style={{ width }}
                  />
                </div>

                <strong className="finance-bar-value">
                  {formatCurrency(entry.net_amount)}
                </strong>
              </div>
            );
          })
        }
      </div>
    </article>
  );
}


function FinanceSeasonCard({
  entry,
  draft,
  onDraftChange,
}: {
  entry: FinanceLeagueSeasonEntry;
  draft: FinanceDraft;
  onDraftChange: (
    nextDraft: FinanceDraft,
  ) => void;
}) {
  return (
    <article className="finance-card">
      <header className="finance-card-header">
        <div>
          <p className="finance-card-kicker">
            {entry.season}
          </p>
          <h2 className="finance-card-title">
            {entry.league_name}
          </h2>
          <p className="finance-card-subtitle">
            {
              entry.rank !== null
                ? `Rank ${entry.rank} of ${entry.total_rosters}`
                : `${entry.total_rosters} teams`
            }
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
        </div>
        <div>
          <span>Winnings</span>
          <strong>{formatCurrency(entry.winnings_amount)}</strong>
        </div>
        <div>
          <span>
            {
              entry.projected_winnings_source === 'historical_rank'
                ? 'Projected payout from historical rank'
                : 'Projected current payout'
            }
          </span>
          <strong>{formatCurrency(entry.projected_winnings_amount)}</strong>
        </div>
      </div>

      <div className="finance-form-grid">
        <label>
          <span>Buy-in amount</span>
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

        <label>
          <span>Winnings</span>
          <input
            type="number"
            min="0"
            step="1"
            value={draft.winningsAmount}
            onChange={(event) => {
              onDraftChange({
                ...draft,
                winningsAmount: event.target.value,
              });
            }}
          />
        </label>
      </div>
    </article>
  );
}


export function FinancePage() {
  const connection = useSleeperConnection();
  const finance = useFinanceSummary(
    connection.linked,
  );
  const saveFinanceMutation = useSaveFinanceSeason();
  const [drafts, setDrafts] = useState<
    Record<string, FinanceDraft>
  >({});

  useEffect(() => {
    if (!finance.data) {
      return;
    }

    setDrafts(
      buildDrafts(
        finance.data.seasons,
      ),
    );
  }, [finance.data]);

  const dirtyEntries = useMemo(
    () => finance.data?.seasons.filter((entry) => (
      isDraftDirty(
        entry,
        drafts[getDraftKey(entry)],
      )
    )) ?? [],
    [drafts, finance.data],
  );

  const handleSaveAll = async () => {
    if (!finance.data || dirtyEntries.length === 0) {
      notify.success('No finance changes to save.');
      return;
    }

    try {
      for (const entry of dirtyEntries) {
        const draft = drafts[getDraftKey(entry)];

        await saveFinanceMutation.mutateAsync({
          league_id: entry.league_id,
          season: entry.season,
          buy_in_amount: parseDraftAmount(
            draft.buyInAmount,
          ),
          winnings_amount: parseDraftAmount(
            draft.winningsAmount,
          ),
        });
      }

      notify.success('Finance entries saved.');
    } catch {
      notify.error('Unable to save finance entries.');
    }
  };

  return (
    <main className="finance-page">
      <section className="finance-page-header">
        <div>
          <p className="page-eyebrow">Finance</p>
          <h1 className="finance-page-title">
            League finance tracker
          </h1>
          <p className="finance-page-description">
            Track buy-ins, winnings, net results, and current payout
            projections for your linked Sleeper leagues.
          </p>
        </div>
      </section>

      {
        !connection.linked
          ? (
            <div className="finance-empty-state">
              Link a Sleeper account to use the finance tracker.
            </div>
          )
          : null
      }

      {
        connection.linked && finance.loading
          ? (
            <LoadingState
              label="Loading finance tracker..."
              className="finance-empty-state"
            />
          )
          : null
      }

      {
        connection.linked && !finance.loading && finance.error
          ? (
            <div className="finance-empty-state">
              Unable to load finance data.
            </div>
          )
          : null
      }

      {
        finance.data
          ? (
            <>
              <section className="finance-summary-grid">
                <article className="finance-summary-card">
                  <span>Total buy-ins</span>
                  <strong>{formatCurrency(finance.data.total_buy_ins)}</strong>
                </article>

                <article className="finance-summary-card">
                  <span>Total winnings</span>
                  <strong>{formatCurrency(finance.data.total_winnings)}</strong>
                </article>

                <article className="finance-summary-card">
                  <span>Total net</span>
                  <strong>{formatCurrency(finance.data.total_net)}</strong>
                </article>

                <article className="finance-summary-card">
                  <span>Projected current payouts</span>
                  <strong>{formatCurrency(finance.data.projected_current_winnings)}</strong>
                </article>
              </section>

              <section className="finance-chart-grid">
                <FinanceTrendChart
                  entries={finance.data.seasons}
                />
                <FinanceNetChart
                  entries={finance.data.seasons}
                />
              </section>

              <section className="finance-save-bar">
                <div>
                  <p className="finance-save-bar-kicker">
                    Draft changes
                  </p>
                  <strong>
                    {dirtyEntries.length} league
                    {dirtyEntries.length === 1 ? '' : 's'} ready to save
                  </strong>
                </div>

                <button
                  type="button"
                  className="button-primary"
                  disabled={saveFinanceMutation.isPending}
                  onClick={() => {
                    void handleSaveAll();
                  }}
                >
                  {
                    saveFinanceMutation.isPending
                      ? 'Saving...'
                      : 'Save all finance changes'
                  }
                </button>
              </section>

              <section className="finance-season-grid">
                {
                  finance.data.seasons.map((entry) => {
                    const key = getDraftKey(entry);

                    return (
                      <FinanceSeasonCard
                        key={key}
                        entry={entry}
                        draft={drafts[key] ?? {
                          buyInAmount: entry.buy_in_amount.toString(),
                          winningsAmount: entry.winnings_amount.toString(),
                        }}
                        onDraftChange={(nextDraft) => {
                          setDrafts((current) => ({
                            ...current,
                            [key]: nextDraft,
                          }));
                        }}
                      />
                    );
                  })
                }
              </section>
            </>
          )
          : null
      }
    </main>
  );
}
