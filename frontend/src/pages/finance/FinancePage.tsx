import { useEffect, useMemo, useState } from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import {
  useFinanceSummary,
  useResetFinanceSeason,
  useSaveFinanceDefaults,
  useSaveFinanceLeagueDefaults,
  useSaveFinanceSeason,
} from '@/hooks/sleeper/useUsers';
import type {
  FinanceDefaultSettings,
  FinanceLeagueSeasonEntry,
  FinancePlacePayout,
} from '@/types';
import { formatNumber } from '@/utils/format';
import { notify } from '@/utils/notify';

import './FinancePage.css';


type FinanceTab =
  | 'charts'
  | 'settings'
  | 'overrides';

type FinanceDraftRow = {
  place: string;
  amount: string;
};

type FinanceSettingsDraft = {
  buyInAmount: string;
  payoutStructure: FinanceDraftRow[];
};

type FinanceSeasonDraft = FinanceSettingsDraft & {
  isExcluded: boolean;
};

type FinanceChartEntry = {
  key: string;
  label: string;
  subLabel: string;
  winningsAmount: number;
  projectedWinningsAmount: number;
  netAmount: number;
};

type FinanceTimelinePoint = {
  week: number;
  label: string;
  actualAmount: number | null;
  projectedAmount: number;
};

const TRACKER_VISIBLE_STATUSES = new Set([
  'pre_draft',
  'drafting',
  'in_season',
  'post_season',
]);


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


function parseAmount(
  value: string,
) {
  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed
    : 0;
}


function parseNullableAmount(
  value: string,
) {
  const trimmed = value.trim();

  if (!trimmed) {
    return null;
  }

  const parsed = Number(trimmed);
  return Number.isFinite(parsed)
    ? parsed
    : null;
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


function buildSettingsDraft(
  settings: FinanceDefaultSettings | {
    buy_in_amount: number | null;
    payout_structure: FinancePlacePayout[];
  },
) {
  return {
    buyInAmount: settings.buy_in_amount?.toString() ?? '',
    payoutStructure: buildPayoutRows(
      settings.payout_structure,
    ),
  };
}


function buildSeasonDrafts(
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
        isExcluded: entry.is_excluded,
      },
    ]),
  ) as Record<string, FinanceSeasonDraft>;
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


function addPayoutRow(
  draft: FinanceSettingsDraft,
) {
  const nextPlace = (
    draft.payoutStructure.length
      ? Math.max(
          ...draft.payoutStructure.map((row) => (
            parseAmount(row.place)
          )),
        ) + 1
      : 1
  );

  return {
    ...draft,
    payoutStructure: [
      ...draft.payoutStructure,
      {
        place: nextPlace.toString(),
        amount: '',
      },
    ],
  };
}


function sourceLabel(
  source: string,
) {
  switch (source) {
    case 'season_override':
      return 'Season override';
    case 'league_default':
      return 'League default';
    case 'global_default':
      return 'Global default';
    case 'commissioner_dues':
      return 'Commissioner dues';
    default:
      return 'Not set';
  }
}

function projectionSourceLabel(
  source: FinanceLeagueSeasonEntry['projected_winnings_source'],
) {
  switch (source) {
    case 'seed_probability':
      return 'Seed probability';
    case 'historical_rank':
      return 'Historical finish';
    case 'configured_place':
      return 'Configured place';
    case 'no_projection':
      return 'No projection';
    default:
      return 'Heuristic';
  }
}

function financeResultLabel(
  entry: FinanceLeagueSeasonEntry,
) {
  if (entry.finish_place !== null) {
    return `Finish ${ordinal(entry.finish_place)} of ${entry.total_rosters}`;
  }

  if (entry.rank !== null) {
    return `Current rank ${ordinal(entry.rank)} of ${entry.total_rosters}`;
  }

  return `${entry.total_rosters} teams`;
}

function isFinanceSeasonComplete(
  entry: FinanceLeagueSeasonEntry,
) {
  return entry.status === 'complete';
}

function effectiveFinanceWinnings(
  entry: FinanceLeagueSeasonEntry,
) {
  return isFinanceSeasonComplete(entry)
    ? entry.winnings_amount
    : entry.projected_winnings_amount;
}

function effectiveFinanceNet(
  entry: FinanceLeagueSeasonEntry,
) {
  return effectiveFinanceWinnings(entry) - entry.buy_in_amount;
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

function buildSeasonChartEntries(
  entries: FinanceLeagueSeasonEntry[],
): FinanceChartEntry[] {
  const bySeason = new Map<
    string,
    {
      winningsAmount: number;
      projectedWinningsAmount: number;
      netAmount: number;
      leagueCount: number;
    }
  >();

  for (const entry of entries) {
    const current = bySeason.get(entry.season) ?? {
      winningsAmount: 0,
      projectedWinningsAmount: 0,
      netAmount: 0,
      leagueCount: 0,
    };

    current.winningsAmount += effectiveFinanceWinnings(entry);
    current.projectedWinningsAmount += entry.projected_winnings_amount;
    current.netAmount += effectiveFinanceNet(entry);
    current.leagueCount += 1;

    bySeason.set(entry.season, current);
  }

  return Array.from(bySeason.entries())
    .map(([season, totals]) => ({
      key: season,
      label: season,
      subLabel: `${totals.leagueCount} ${
        totals.leagueCount === 1 ? 'league' : 'leagues'
      }`,
      winningsAmount: totals.winningsAmount,
      projectedWinningsAmount: totals.projectedWinningsAmount,
      netAmount: totals.netAmount,
    }))
    .sort((left, right) => (
      Number(left.label) - Number(right.label)
    ));
}

function buildCurrentFinanceTimeline(
  entries: FinanceLeagueSeasonEntry[],
): FinanceTimelinePoint[] {
  if (!entries.length) {
    return [];
  }

  return [
    {
      week: 1,
      label: 'Week 1',
      actualAmount: entries.reduce(
        (sum, entry) => sum + effectiveFinanceWinnings(entry),
        0,
      ),
      projectedAmount: entries.reduce(
        (sum, entry) => sum + entry.projected_winnings_amount,
        0,
      ),
    },
  ];
}


function FinanceTrendChart({
  entries,
}: {
  entries: FinanceChartEntry[];
}) {
  const actualPoints = buildLinePoints(
    entries.map((entry) => entry.winningsAmount),
    320,
    140,
  );
  const projectedPoints = buildLinePoints(
    entries.map((entry) => entry.projectedWinningsAmount),
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
            entries.map((entry) => (
              <span key={entry.key}>
                {entry.label}
              </span>
            ))
          }
        </div>
      </div>
    </article>
  );
}

function FinanceProjectionTimeline({
  entries,
  season,
}: {
  entries: FinanceLeagueSeasonEntry[];
  season: string;
}) {
  const points = buildCurrentFinanceTimeline(entries);
  const actualPoints = buildLinePoints(
    points.map((point) => point.actualAmount ?? 0),
    320,
    140,
  );
  const projectedPoints = buildLinePoints(
    points.map((point) => point.projectedAmount),
    320,
    140,
  );
  const latest = points[points.length - 1];

  return (
    <article className="finance-chart-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">Weekly projection</p>
          <h2>{season} payout trajectory</h2>
        </div>
      </div>

      <div className="finance-chart-legend">
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-actual" />
          Actual payout
        </span>
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-projected" />
          Expected payout
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
            points.map((point) => (
              <span key={point.week}>
                {point.label}
              </span>
            ))
          }
        </div>
      </div>

      <div className="finance-timeline-note">
        <strong>
          {
            latest
              ? formatCurrency(latest.projectedAmount)
              : formatCurrency(0)
          }
        </strong>
        <span>
          Current expected payout snapshot. Weekly snapshots are not
          persisted yet, so this will grow once the sync stores weekly
          finance history.
        </span>
      </div>
    </article>
  );
}


function FinanceNetChart({
  entries,
}: {
  entries: FinanceChartEntry[];
}) {
  const maxMagnitude = Math.max(
    ...entries.map((entry) => Math.abs(entry.netAmount)),
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
          entries.map((entry) => (
            <div
              key={entry.key}
              className="finance-bar-row"
            >
              <div className="finance-bar-copy">
                <strong>{entry.label}</strong>
                <span>{entry.subLabel}</span>
              </div>

              <div className="finance-bar-track">
                <div
                  className={
                    entry.netAmount >= 0
                      ? 'finance-bar finance-bar-positive'
                      : 'finance-bar finance-bar-negative'
                  }
                  style={{
                    width: `${(Math.abs(entry.netAmount) / maxMagnitude) * 100}%`,
                  }}
                />
              </div>

              <strong className="finance-bar-value">
                {formatCurrency(entry.netAmount)}
              </strong>
            </div>
          ))
        }
      </div>
    </article>
  );
}

function FinanceLeagueBreakdown({
  entries,
}: {
  entries: FinanceLeagueSeasonEntry[];
}) {
  const sortedEntries = [...entries].sort((left, right) => (
    effectiveFinanceNet(right) - effectiveFinanceNet(left)
  ));

  return (
    <article className="finance-chart-card finance-league-breakdown-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">League results</p>
          <h2>League net breakdown</h2>
        </div>
      </div>

      <div className="finance-league-breakdown">
        {
          sortedEntries.map((entry) => (
            <div
              key={getDraftKey(entry)}
              className="finance-league-breakdown-row"
            >
              <div>
                <strong>{entry.league_name}</strong>
                <span>{financeResultLabel(entry)}</span>
              </div>
              <div>
                <span>Net</span>
                <strong>{formatCurrency(effectiveFinanceNet(entry))}</strong>
              </div>
              <div>
                <span>
                  {
                    isFinanceSeasonComplete(entry)
                      ? 'Finish payout'
                      : 'Expected payout'
                  }
                </span>
                <strong>{formatCurrency(effectiveFinanceWinnings(entry))}</strong>
              </div>
              <div>
                <span>Buy-in</span>
                <strong>{formatCurrency(entry.buy_in_amount)}</strong>
              </div>
            </div>
          ))
        }
      </div>
    </article>
  );
}


function FinancePayoutEditor({
  draft,
  onChange,
}: {
  draft: FinanceSettingsDraft;
  onChange: (
    nextDraft: FinanceSettingsDraft,
  ) => void;
}) {
  return (
    <div className="finance-payout-editor">
      <div className="finance-payout-editor-header">
        <span>Payout structure</span>

        <button
          type="button"
          className="button-secondary"
          onClick={() => {
            onChange(
              addPayoutRow(draft),
            );
          }}
        >
          Add place
        </button>
      </div>

      <div className="finance-payout-rows">
        {
          draft.payoutStructure.map((row, index) => (
            <div
              key={`${row.place}-${index}`}
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
                    onChange({
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
                    onChange({
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
                  onChange({
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
  );
}


function FinanceSeasonCard({
  entry,
  draft,
  onDraftChange,
  onReset,
  resetPending,
}: {
  entry: FinanceLeagueSeasonEntry;
  draft: FinanceSeasonDraft;
  onDraftChange: (
    nextDraft: FinanceSeasonDraft,
  ) => void;
  onReset: () => void;
  resetPending: boolean;
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
            {
              entry.projected_finish_place !== null
                ? `Projected seed ${ordinal(entry.projected_finish_place)} · `
                : ''
            }
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
    })).sort((left, right) => (
      left.leagueName.localeCompare(right.leagueName)
    ));
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
      <section className="finance-page-header">
        <div>
          <p className="page-eyebrow">Finance</p>
          <h1 className="finance-page-title">
            League finance tracker
          </h1>
          <p className="finance-page-description">
            Set global defaults once, bulk-apply league-specific settings where
            needed, and only use season overrides when a year was different.
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
                        </article>

                        <article className="finance-summary-card">
                          <span>Total net</span>
                          <strong>{formatCurrency(overviewSummary.totalNet)}</strong>
                        </article>

                        <article className="finance-summary-card">
                          <span>Expected payouts</span>
                          <strong>{formatCurrency(overviewSummary.projectedCurrentWinnings)}</strong>
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
