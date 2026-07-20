import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Wallet } from 'lucide-react';

import { Skeleton } from '@/components/feedback/Skeleton';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import {
  useFinanceSummary,
  useResetFinanceSeason,
  useSaveFinanceDefaults,
  useSaveFinanceLeagueDefaults,
  useSaveFinanceSeason,
} from '@/hooks/sleeper/useUsers';
import type {
  FinanceLeagueSeasonEntry,
} from '@/types';
import { notify } from '@/utils/notify';
import {
  buildPayoutRows,
  buildSeasonChartEntries,
  buildSeasonDrafts,
  buildSettingsDraft,
  draftRowsEqual,
  effectiveFinanceNet,
  effectiveFinanceWinnings,
  formatCurrency,
  getDraftKey,
  isFinanceSeasonComplete,
  normalizeDraftRows,
  parseAmount,
  parseNullableAmount,
  type FinanceSeasonDraft,
  type FinanceSettingsDraft,
} from './finance.utils';
import {
  FinanceLeagueBreakdown,
  FinanceNetChart,
  FinanceProjectionTimeline,
  FinanceTrendChart,
} from './FinanceCharts';
import { FinancePayoutEditor } from './FinancePayoutEditor';
import { FinanceSeasonCard } from './FinanceSeasonCard';

import './FinancePage.css';


type FinanceTab =
  | 'charts'
  | 'settings'
  | 'overrides';

const TRACKER_VISIBLE_STATUSES = new Set([
  'pre_draft',
  'drafting',
  'in_season',
  'post_season',
]);

function FinancePageSkeleton() {
  return (
    <div className="finance-loading-shell" role="status" aria-live="polite">
      <span className="skeleton-sr-label">Loading finance tracker...</span>

      <div className="finance-tabs-row">
        <div className="finance-tabs finance-tabs-skeleton">
          <Skeleton width={92} height={40} />
          <Skeleton width={92} height={40} />
          <Skeleton width={92} height={40} />
        </div>

        <div className="finance-overview-controls">
          <label>
            <span>Year</span>
            <Skeleton width={260} height={46} />
          </label>
        </div>
      </div>

      <section className="finance-summary-grid">
        {
          Array.from({ length: 4 }).map((_, index) => (
            <article className="finance-summary-card" key={index}>
              <Skeleton width={130} variant="text" />
              <Skeleton width={92} height={28} />
            </article>
          ))
        }
      </section>

      <section className="finance-chart-grid">
        <article className="finance-chart-card">
          <Skeleton width={88} variant="text" />
          <Skeleton width={240} variant="title" />
          <div className="finance-skeleton-chart">
            <Skeleton width="100%" height={180} />
          </div>
        </article>

        <article className="finance-chart-card">
          <Skeleton width={64} variant="text" />
          <Skeleton width={210} variant="title" />
          <div className="finance-skeleton-bars">
            {
              Array.from({ length: 5 }).map((_, index) => (
                <div className="finance-skeleton-bar-row" key={index}>
                  <div>
                    <Skeleton width={56} variant="text" />
                    <Skeleton width={88} variant="text" />
                  </div>
                  <Skeleton width={`${80 - index * 10}%`} height={14} />
                  <Skeleton width={58} variant="text" />
                </div>
              ))
            }
          </div>
        </article>
      </section>
    </div>
  );
}

export function FinancePage() {
  const connection = useSleeperConnection();
  const finance = useFinanceSummary(
    connection.linked,
  );
  const saveFinanceMutation = useSaveFinanceSeason();
  const resetFinanceMutation = useResetFinanceSeason();
  const saveDefaultsMutation = useSaveFinanceDefaults();
  const saveLeagueDefaultsMutation = useSaveFinanceLeagueDefaults();
  const [activeTab, setActiveTab] = useState<FinanceTab>('charts');
  const [selectedTrackerSeason, setSelectedTrackerSeason] = useState('current');
  const [chartSeason, setChartSeason] = useState('all');
  const [seasonDrafts, setSeasonDrafts] = useState<
    Record<string, FinanceSeasonDraft>
  >({});
  const [globalDraft, setGlobalDraft] = useState<FinanceSettingsDraft>({
    buyInAmount: '',
    payoutStructure: buildPayoutRows([]),
  });
  const [bulkDraft, setBulkDraft] = useState<FinanceSettingsDraft>({
    buyInAmount: '',
    payoutStructure: buildPayoutRows([]),
  });
  const [selectedLeagueFamilies, setSelectedLeagueFamilies] = useState<string[]>([]);

  useEffect(() => {
    if (!finance.data) {
      return;
    }

    setSeasonDrafts(
      buildSeasonDrafts(finance.data.seasons),
    );
    setGlobalDraft(
      buildSettingsDraft(finance.data.defaults),
    );
    setBulkDraft(
      buildSettingsDraft(finance.data.defaults),
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

  const trackerEntries = useMemo(
    () => (
      finance.data?.seasons.filter((entry) => {
        if (selectedTrackerSeason === 'current') {
          return TRACKER_VISIBLE_STATUSES.has(
            entry.status,
          );
        }

        return entry.season === selectedTrackerSeason;
      }) ?? []
    ),
    [
      finance.data,
      selectedTrackerSeason,
    ],
  );

  const displayedTrackerEntries = useMemo(() => {
    if (selectedTrackerSeason !== 'current') {
      return trackerEntries;
    }

    const latestByFamily = new Map<string, FinanceLeagueSeasonEntry>();

    for (const entry of trackerEntries) {
      const existing = latestByFamily.get(
        entry.league_family_id,
      );

      if (!existing || Number(entry.season) > Number(existing.season)) {
        latestByFamily.set(
          entry.league_family_id,
          entry,
        );
      }
    }

    return Array.from(
      latestByFamily.values(),
    ).sort((left, right) => (
      left.league_name.localeCompare(right.league_name)
    ));
  }, [
    selectedTrackerSeason,
    trackerEntries,
  ]);

  const chartEntries = useMemo(
    () => (
      finance.data?.seasons.filter((entry) => (
        !entry.is_excluded
        && (
          chartSeason === 'all'
          || entry.season === chartSeason
        )
      )) ?? []
    ),
    [chartSeason, finance.data],
  );

  const seasonChartEntries = useMemo(
    () => buildSeasonChartEntries(chartEntries),
    [chartEntries],
  );

  const overviewHasProjectedEntries = useMemo(
    () => chartEntries.some((entry) => !isFinanceSeasonComplete(entry)),
    [chartEntries],
  );

  const globalDraftDirty = useMemo(() => (
    !!finance.data && (
      parseNullableAmount(globalDraft.buyInAmount) !== finance.data.defaults.buy_in_amount
      || !draftRowsEqual(
        globalDraft.payoutStructure,
        buildPayoutRows(finance.data.defaults.payout_structure),
      )
    )
  ), [finance.data, globalDraft]);

  const dirtyEntries = useMemo(
    () => displayedTrackerEntries.filter((entry) => {
      const draft = seasonDrafts[getDraftKey(entry)];

      if (!draft) {
        return false;
      }

      return (
        parseAmount(draft.buyInAmount) !== entry.buy_in_amount
        || draft.isExcluded !== entry.is_excluded
        || !draftRowsEqual(
          draft.payoutStructure,
          buildPayoutRows(entry.payout_structure),
        )
      );
    }),
    [displayedTrackerEntries, seasonDrafts],
  );

  const uniqueLeagueFamilies = useMemo(() => {
    const seen = new Map<string, string>();

    for (const entry of displayedTrackerEntries) {
      if (!seen.has(entry.league_family_id)) {
        seen.set(
          entry.league_family_id,
          entry.league_name,
        );
      }
    }

    return Array.from(seen.entries()).map(([leagueFamilyId, leagueName]) => ({
      leagueFamilyId,
      leagueName,
    }));
  }, [displayedTrackerEntries]);

  const overviewSummary = useMemo(() => {
    return {
      totalBuyIns: chartEntries.reduce(
        (sum, entry) => sum + entry.buy_in_amount,
        0,
      ),
      totalWinnings: chartEntries.reduce(
        (sum, entry) => sum + effectiveFinanceWinnings(entry),
        0,
      ),
      totalNet: chartEntries.reduce(
        (sum, entry) => sum + effectiveFinanceNet(entry),
        0,
      ),
      projectedCurrentWinnings: chartEntries.reduce(
        (sum, entry) => sum + entry.projected_winnings_amount,
        0,
      ),
    };
  }, [chartEntries]);

  const handleSaveAll = async () => {
    if (!dirtyEntries.length) {
      notify.success('No season overrides to save.');
      return;
    }

    try {
      for (const entry of dirtyEntries) {
        const draft = seasonDrafts[getDraftKey(entry)];

        await saveFinanceMutation.mutateAsync({
          league_id: entry.league_id,
          season: entry.season,
          buy_in_amount: parseAmount(
            draft.buyInAmount,
          ),
          payout_structure: normalizeDraftRows(
            draft.payoutStructure,
          ).map((row) => ({
            place: parseAmount(row.place),
            amount: parseAmount(row.amount),
          })),
          is_excluded: draft.isExcluded,
        });
      }

      notify.success('Season overrides saved.');
    } catch {
      notify.error('Unable to save finance overrides.');
    }
  };

  const handleSaveGlobalDefaults = async () => {
    try {
      await saveDefaultsMutation.mutateAsync({
        buy_in_amount: parseNullableAmount(
          globalDraft.buyInAmount,
        ),
        payout_structure: normalizeDraftRows(
          globalDraft.payoutStructure,
        ).map((row) => ({
          place: parseAmount(row.place),
          amount: parseAmount(row.amount),
        })),
      });
      notify.success('Global finance defaults saved.');
    } catch {
      notify.error('Unable to save global defaults.');
    }
  };

  const handleApplyLeagueDefaults = async () => {
    if (!selectedLeagueFamilies.length) {
      notify.error('Select at least one league.');
      return;
    }

    try {
      await saveLeagueDefaultsMutation.mutateAsync({
        league_family_ids: selectedLeagueFamilies,
        buy_in_amount: parseNullableAmount(
          bulkDraft.buyInAmount,
        ),
        payout_structure: normalizeDraftRows(
          bulkDraft.payoutStructure,
        ).map((row) => ({
          place: parseAmount(row.place),
          amount: parseAmount(row.amount),
        })),
      });
      notify.success('League defaults applied.');
    } catch {
      notify.error('Unable to apply league defaults.');
    }
  };

  return (
    <main className="finance-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Finance</p>
          <h1 className="page-title">
            League finance tracker
          </h1>
          <p className="page-description">
            Set global defaults once, bulk-apply league-specific settings where
            needed, and only use season overrides when a year was different.
          </p>
        </div>
      </section>

      {
        !connection.linked
          ? (
            <div className="empty-state">
              <Wallet size={32} className="empty-state-icon" />
              <p className="empty-state-title">Link your account</p>
              <p className="empty-state-message">
                Link a Sleeper account to use the finance tracker.
              </p>
            </div>
          )
          : null
      }

      {
        connection.linked && finance.loading
          ? (
            <FinancePageSkeleton />
          )
          : null
      }

      {
        connection.linked && !finance.loading && finance.error
          ? (
            <div className="empty-state">
              <AlertTriangle size={32} className="empty-state-icon" />
              <p className="empty-state-title">Unable to load finance data</p>
              <p className="empty-state-message">
                Please try again later.
              </p>
            </div>
          )
          : null
      }

      {
        finance.data
          ? (
            <>
              <div className="finance-tabs-row">
                <div className="finance-tabs" role="tablist" aria-label="Finance tabs">
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
                    Overview
                  </button>
                  <button
                    type="button"
                    className={
                      activeTab === 'settings'
                        ? 'finance-tab active'
                        : 'finance-tab'
                    }
                    onClick={() => {
                      setActiveTab('settings');
                    }}
                  >
                    Settings
                  </button>
                  <button
                    type="button"
                    className={
                      activeTab === 'overrides'
                        ? 'finance-tab active'
                        : 'finance-tab'
                    }
                    onClick={() => {
                      setActiveTab('overrides');
                    }}
                  >
                    Overrides
                  </button>
                </div>

                {
                  activeTab === 'charts'
                    ? (
                      <div className="finance-overview-controls">
                        <label>
                          <span>Year</span>
                          <select
                            value={chartSeason}
                            onChange={(event) => {
                              setChartSeason(event.target.value);
                            }}
                          >
                            <option value="all">All years</option>
                            {
                              availableSeasons.map((season) => (
                                <option key={season} value={season}>
                                  {season}
                                </option>
                              ))
                            }
                          </select>
                        </label>
                      </div>
                    )
                    : null
                }
              </div>

              {
                activeTab === 'settings'
                  ? (
                    <>
                      <section className="finance-settings-grid">
                        <article className="finance-settings-card">
                          <header className="finance-settings-header">
                            <div>
                              <p className="finance-card-kicker">Defaults</p>
                              <h2>Global finance defaults</h2>
                            </div>

                            <button
                              type="button"
                              className="button-primary"
                              disabled={
                                !globalDraftDirty
                                || saveDefaultsMutation.isPending
                              }
                              onClick={() => {
                                void handleSaveGlobalDefaults();
                              }}
                            >
                              {
                                saveDefaultsMutation.isPending
                                  ? 'Saving...'
                                  : 'Save defaults'
                              }
                            </button>
                          </header>

                          <div className="finance-form-grid">
                            <label>
                              <span>Default buy-in</span>
                              <input
                                type="number"
                                min="0"
                                step="1"
                                placeholder="Unset"
                                value={globalDraft.buyInAmount}
                                onChange={(event) => {
                                  setGlobalDraft((current) => ({
                                    ...current,
                                    buyInAmount: event.target.value,
                                  }));
                                }}
                              />
                            </label>
                          </div>

                          <FinancePayoutEditor
                            draft={globalDraft}
                            onChange={setGlobalDraft}
                          />
                        </article>

                        <article className="finance-settings-card">
                          <header className="finance-settings-header">
                            <div>
                              <p className="finance-card-kicker">Bulk apply</p>
                              <h2>League-specific defaults</h2>
                            </div>

                            <button
                              type="button"
                              className="button-primary"
                              disabled={
                                saveLeagueDefaultsMutation.isPending
                              }
                              onClick={() => {
                                void handleApplyLeagueDefaults();
                              }}
                            >
                              {
                                saveLeagueDefaultsMutation.isPending
                                  ? 'Applying...'
                                  : `Apply to ${selectedLeagueFamilies.length || ''} leagues`
                              }
                            </button>
                          </header>

                          <div className="finance-form-grid">
                            <label>
                              <span>League buy-in default</span>
                              <input
                                type="number"
                                min="0"
                                step="1"
                                placeholder="Unset"
                                value={bulkDraft.buyInAmount}
                                onChange={(event) => {
                                  setBulkDraft((current) => ({
                                    ...current,
                                    buyInAmount: event.target.value,
                                  }));
                                }}
                              />
                            </label>
                          </div>

                          <FinancePayoutEditor
                            draft={bulkDraft}
                            onChange={setBulkDraft}
                          />

                          <div className="finance-league-selector">
                            <div className="finance-league-selector-actions">
                              <button
                                type="button"
                                className="button-secondary"
                                onClick={() => {
                                  setSelectedLeagueFamilies(
                                    uniqueLeagueFamilies.map((league) => (
                                      league.leagueFamilyId
                                    )),
                                  );
                                }}
                              >
                                Select all
                              </button>
                              <button
                                type="button"
                                className="button-secondary"
                                onClick={() => {
                                  setSelectedLeagueFamilies([]);
                                }}
                              >
                                Deselect all
                              </button>
                            </div>

                            <div className="finance-league-selector-list">
                            {
                              uniqueLeagueFamilies.map((league) => (
                                <div
                                  key={league.leagueFamilyId}
                                  className="finance-league-option"
                                >
                                  <label
                                    className="finance-league-checkbox"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={selectedLeagueFamilies.includes(
                                        league.leagueFamilyId,
                                      )}
                                      onChange={(event) => {
                                        setSelectedLeagueFamilies((current) => (
                                          event.target.checked
                                            ? [
                                                ...current,
                                                league.leagueFamilyId,
                                              ]
                                            : current.filter(
                                                (value) => value !== league.leagueFamilyId,
                                              )
                                        ));
                                      }}
                                    />
                                  </label>
                                  <button
                                    type="button"
                                    className="finance-league-name-button"
                                    onClick={() => {
                                      setSelectedLeagueFamilies((current) => (
                                        current.includes(
                                          league.leagueFamilyId,
                                        )
                                          ? current.filter(
                                              (value) => value !== league.leagueFamilyId,
                                            )
                                          : [
                                              ...current,
                                              league.leagueFamilyId,
                                            ]
                                      ));
                                    }}
                                  >
                                    {league.leagueName}
                                  </button>
                                </div>
                              ))
                            }
                            </div>
                          </div>
                        </article>
                      </section>
                    </>
                  )
                  : activeTab === 'overrides'
                    ? (
                      <>
                        <section className="finance-toolbar">
                          <label>
                            <span>Override year</span>
                            <select
                              value={selectedTrackerSeason}
                              onChange={(event) => {
                                setSelectedTrackerSeason(
                                  event.target.value,
                                );
                              }}
                            >
                              <option value="current">Current leagues</option>
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
                                : `Save ${dirtyEntries.length || ''} season overrides`
                            }
                          </button>
                        </section>

                        <section className="finance-season-grid">
                          {
                            displayedTrackerEntries.map((entry) => {
                              const key = getDraftKey(entry);

                              return (
                                <FinanceSeasonCard
                                  key={key}
                                  entry={entry}
                                  draft={seasonDrafts[key] ?? {
                                    buyInAmount: entry.buy_in_amount.toString(),
                                    payoutStructure: buildPayoutRows(
                                      entry.payout_structure,
                                    ),
                                    isExcluded: entry.is_excluded,
                                  }}
                                  onDraftChange={(nextDraft) => {
                                    setSeasonDrafts((current) => ({
                                      ...current,
                                      [key]: nextDraft,
                                    }));
                                  }}
                                  onReset={() => {
                                    void resetFinanceMutation.mutateAsync({
                                      league_id: entry.league_id,
                                      season: entry.season,
                                    }).catch(() => {
                                      notify.error('Unable to reset season override.');
                                    });
                                  }}
                                  resetPending={resetFinanceMutation.isPending}
                                />
                              );
                            })
                          }
                        </section>
                      </>
                    )
                  : (
                    <>
                      <section className="finance-summary-grid">
                        <article className="finance-summary-card">
                          <span>Total buy-ins</span>
                          <strong>{formatCurrency(overviewSummary.totalBuyIns)}</strong>
                        </article>

                        <article className="finance-summary-card">
                          <span>Total winnings</span>
                          <strong>{formatCurrency(overviewSummary.totalWinnings)}</strong>
                          {
                            overviewHasProjectedEntries
                              ? <small>Includes expected payouts for active seasons.</small>
                              : null
                          }
                        </article>

                        <article className="finance-summary-card">
                          <span>Total net</span>
                          <strong>{formatCurrency(overviewSummary.totalNet)}</strong>
                          {
                            overviewHasProjectedEntries
                              ? <small>Projected until seasons are complete.</small>
                              : null
                          }
                        </article>

                        <article className="finance-summary-card">
                          <span>Expected payouts</span>
                          <strong>{formatCurrency(overviewSummary.projectedCurrentWinnings)}</strong>
                          {
                            overviewHasProjectedEntries
                              ? <small>Projected from seed probability.</small>
                              : null
                          }
                        </article>
                      </section>

                      <section className="finance-chart-grid">
                        {
                          chartSeason === 'all'
                            ? (
                              <FinanceTrendChart
                                entries={seasonChartEntries}
                              />
                            )
                            : (
                              <FinanceProjectionTimeline
                                entries={chartEntries}
                                season={chartSeason}
                              />
                            )
                        }
                        {
                          chartSeason === 'all'
                            ? (
                              <FinanceNetChart
                                entries={seasonChartEntries}
                              />
                            )
                            : (
                              <FinanceLeagueBreakdown
                                entries={chartEntries}
                              />
                            )
                        }
                      </section>
                    </>
                  )
              }
            </>
          )
          : null
      }
    </main>
  );
}
