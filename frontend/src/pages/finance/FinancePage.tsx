import { useEffect, useMemo, useState } from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import {
  useFinanceSummary,
  useSaveFinanceSeason,
} from '@/hooks/sleeper/useUsers';
import type {
  FinanceLeagueSeasonEntry,
  FinancePlacePayout,
} from '@/types';
import { formatNumber } from '@/utils/format';
import { notify } from '@/utils/notify';

import './FinancePage.css';


type FinanceTab =
  | 'tracker'
  | 'charts';

type FinanceDraftRow = {
  place: string;
  amount: string;
};

type FinanceDraft = {
  buyInAmount: string;
  payoutStructure: FinanceDraftRow[];
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


function ordinal(
  value: number,
) {
  const mod10 = value % 10;
  const mod100 = value % 100;

  if (mod10 === 1 && mod100 !== 11) {
    return `${value}st`;
  }

  if (mod10 === 2 && mod100 !== 12) {
    return `${value}nd`;
  }

  if (mod10 === 3 && mod100 !== 13) {
    return `${value}rd`;
  }

  return `${value}th`;
}


function getDraftKey(
  entry: FinanceLeagueSeasonEntry,
) {
  return `${entry.league_id}-${entry.season}`;
}


function buildPayoutRows(
  payouts: FinancePlacePayout[],
) {
  if (!payouts.length) {
    return [
      {
        place: '1',
        amount: '',
      },
    ];
  }

  return payouts.map((payout) => ({
    place: payout.place.toString(),
    amount: payout.amount
      ? payout.amount.toString()
      : '',
  }));
}


function buildDrafts(
  entries: FinanceLeagueSeasonEntry[],
) {
  return Object.fromEntries(
    entries.map((entry) => [
      getDraftKey(entry),
      {
        buyInAmount: entry.buy_in_amount.toString(),
        payoutStructure: buildPayoutRows(
          entry.payout_structure,
        ),
      },
    ]),
  ) as Record<string, FinanceDraft>;
}


function parseAmount(
  value: string,
) {
  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed
    : 0;
}


function normalizeDraftRows(
  rows: FinanceDraftRow[],
) {
  return rows
    .map((row) => ({
      place: parseAmount(row.place).toString(),
      amount: row.amount,
    }))
    .filter((row) => parseAmount(row.place) > 0)
    .sort((left, right) => (
      parseAmount(left.place) - parseAmount(right.place)
    ));
}


function draftRowsEqual(
  left: FinanceDraftRow[],
  right: FinanceDraftRow[],
) {
  const leftRows = normalizeDraftRows(left);
  const rightRows = normalizeDraftRows(right);

  if (leftRows.length !== rightRows.length) {
    return false;
  }

  return leftRows.every((row, index) => (
    row.place === rightRows[index].place
    && parseAmount(row.amount) === parseAmount(rightRows[index].amount)
  ));
}


function isDraftDirty(
  entry: FinanceLeagueSeasonEntry,
  draft: FinanceDraft | undefined,
) {
  if (!draft) {
    return false;
  }

  return (
    parseAmount(draft.buyInAmount) !== entry.buy_in_amount
    || !draftRowsEqual(
      draft.payoutStructure,
      buildPayoutRows(entry.payout_structure),
    )
  );
}


function buildLinePoints(
  values: number[],
  width: number,
  height: number,
) {
  if (!values.length) {
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
  const actualPoints = buildLinePoints(
    chartEntries.map((entry) => entry.winnings_amount),
    320,
    140,
  );
  const projectedPoints = buildLinePoints(
    chartEntries.map((entry) => entry.projected_winnings_amount),
    320,
    140,
  );

  return (
    <article className="finance-chart-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">Trend</p>
          <h2>Results vs projected winnings</h2>
        </div>
      </div>

      <div className="finance-chart-legend">
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-actual" />
          Finish payout
        </span>
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-projected" />
          Projected payout
        </span>
      </div>

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
        </svg>

        <div className="finance-chart-label-row">
          {
            chartEntries.map((entry) => (
              <span key={getDraftKey(entry)}>
                {entry.season}
              </span>
            ))
          }
        </div>
      </div>
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
          <p className="finance-chart-kicker">Net</p>
          <h2>Season net results</h2>
        </div>
      </div>

      <div className="finance-bar-chart">
        {
          chartEntries.map((entry) => (
            <div
              key={getDraftKey(entry)}
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
                  style={{
                    width: `${(Math.abs(entry.net_amount) / maxMagnitude) * 100}%`,
                  }}
                />
              </div>

              <strong className="finance-bar-value">
                {formatCurrency(entry.net_amount)}
              </strong>
            </div>
          ))
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
          <p className="finance-card-kicker">{entry.season}</p>
          <h2 className="finance-card-title">
            {entry.league_name}
          </h2>
          <p className="finance-card-subtitle">
            {
              entry.finish_place !== null
                ? `Finish ${ordinal(entry.finish_place)} of ${entry.total_rosters}`
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
          <span>Finish payout</span>
          <strong>{formatCurrency(entry.winnings_amount)}</strong>
        </div>
        <div>
          <span>
            {
              entry.projected_finish_place !== null
                ? `Projected ${ordinal(entry.projected_finish_place)} payout`
                : 'Projected payout'
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
      </div>

      <div className="finance-payout-editor">
        <div className="finance-payout-editor-header">
          <span>Payout structure</span>

          <button
            type="button"
            className="button-secondary"
            onClick={() => {
              const nextPlace = (
                draft.payoutStructure.length
                  ? Math.max(
                      ...draft.payoutStructure.map((row) => (
                        parseAmount(row.place)
                      )),
                    ) + 1
                  : 1
              );

              onDraftChange({
                ...draft,
                payoutStructure: [
                  ...draft.payoutStructure,
                  {
                    place: nextPlace.toString(),
                    amount: '',
                  },
                ],
              });
            }}
          >
            Add place
          </button>
        </div>

        <div className="finance-payout-rows">
          {
            draft.payoutStructure.map((row, index) => (
              <div
                key={`${getDraftKey(entry)}-${index}`}
                className="finance-payout-row"
              >
                <label>
                  <span>Place</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={row.place}
                    onChange={(event) => {
                      const nextRows = [...draft.payoutStructure];
                      nextRows[index] = {
                        ...row,
                        place: event.target.value,
                      };
                      onDraftChange({
                        ...draft,
                        payoutStructure: nextRows,
                      });
                    }}
                  />
                </label>

                <label>
                  <span>{ordinal(parseAmount(row.place) || 1)} payout</span>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={row.amount}
                    onChange={(event) => {
                      const nextRows = [...draft.payoutStructure];
                      nextRows[index] = {
                        ...row,
                        amount: event.target.value,
                      };
                      onDraftChange({
                        ...draft,
                        payoutStructure: nextRows,
                      });
                    }}
                  />
                </label>

                <button
                  type="button"
                  className="button-secondary"
                  disabled={draft.payoutStructure.length === 1}
                  onClick={() => {
                    onDraftChange({
                      ...draft,
                      payoutStructure: draft.payoutStructure.filter(
                        (_, rowIndex) => rowIndex !== index,
                      ),
                    });
                  }}
                >
                  Remove
                </button>
              </div>
            ))
          }
        </div>
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
  const [activeTab, setActiveTab] = useState<FinanceTab>('tracker');
  const [selectedSeason, setSelectedSeason] = useState('all');
  const [drafts, setDrafts] = useState<
    Record<string, FinanceDraft>
  >({});

  useEffect(() => {
    if (!finance.data) {
      return;
    }

    setDrafts(
      buildDrafts(finance.data.seasons),
    );
  }, [finance.data]);

  const availableSeasons = useMemo(
    () => Array.from(
      new Set(
        finance.data?.seasons.map((entry) => entry.season) ?? [],
      ),
    ).sort((left, right) => Number(right) - Number(left)),
    [finance.data],
  );

  const filteredEntries = useMemo(
    () => finance.data?.seasons.filter((entry) => (
      selectedSeason === 'all'
      || entry.season === selectedSeason
    )) ?? [],
    [finance.data, selectedSeason],
  );

  const dirtyEntries = useMemo(
    () => filteredEntries.filter((entry) => (
      isDraftDirty(
        entry,
        drafts[getDraftKey(entry)],
      )
    )),
    [drafts, filteredEntries],
  );

  const handleSaveAll = async () => {
    if (!dirtyEntries.length) {
      notify.success('No finance changes to save.');
      return;
    }

    try {
      for (const entry of dirtyEntries) {
        const draft = drafts[getDraftKey(entry)];

        await saveFinanceMutation.mutateAsync({
          league_id: entry.league_id,
          season: entry.season,
          buy_in_amount: parseAmount(
            draft.buyInAmount,
          ),
          winnings_amount: entry.winnings_amount,
          payout_structure: normalizeDraftRows(
            draft.payoutStructure,
          ).map((row) => ({
            place: parseAmount(row.place),
            amount: parseAmount(row.amount),
          })),
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
            Track buy-ins and payout structures so dynasty results and current
            projected winnings can be derived from your finish.
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
              <div className="finance-tabs" role="tablist" aria-label="Finance tabs">
                <button
                  type="button"
                  className={
                    activeTab === 'tracker'
                      ? 'finance-tab active'
                      : 'finance-tab'
                  }
                  onClick={() => {
                    setActiveTab('tracker');
                  }}
                >
                  Tracker
                </button>
                <button
                  type="button"
                  className={
                    activeTab === 'charts'
                      ? 'finance-tab active'
                      : 'finance-tab'
                  }
                  onClick={() => {
                    setActiveTab('charts');
                  }}
                >
                  Charts
                </button>
              </div>

              {
                activeTab === 'tracker'
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

                      <section className="finance-toolbar">
                        <label>
                          <span>Season</span>
                          <select
                            value={selectedSeason}
                            onChange={(event) => {
                              setSelectedSeason(event.target.value);
                            }}
                          >
                            <option value="all">All seasons</option>
                            {
                              availableSeasons.map((season) => (
                                <option key={season} value={season}>
                                  {season}
                                </option>
                              ))
                            }
                          </select>
                        </label>

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
                              : `Save ${dirtyEntries.length || ''} finance changes`
                          }
                        </button>
                      </section>

                      <section className="finance-season-grid">
                        {
                          filteredEntries.map((entry) => {
                            const key = getDraftKey(entry);

                            return (
                              <FinanceSeasonCard
                                key={key}
                                entry={entry}
                                draft={drafts[key] ?? {
                                  buyInAmount: entry.buy_in_amount.toString(),
                                  payoutStructure: buildPayoutRows(
                                    entry.payout_structure,
                                  ),
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
                  : (
                    <section className="finance-chart-grid">
                      <FinanceTrendChart
                        entries={finance.data.seasons}
                      />
                      <FinanceNetChart
                        entries={finance.data.seasons}
                      />
                    </section>
                  )
              }
            </>
          )
          : null
      }
    </main>
  );
}
