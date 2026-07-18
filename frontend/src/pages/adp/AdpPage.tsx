import './AdpPage.css';

import { useDeferredValue, useMemo, useState } from 'react';
import { Database, Filter } from 'lucide-react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useAdp } from '@/hooks/useAdp';
import { useAdpMetadata } from '@/hooks/useAdpMetadata';
import type {
  ADPDistributionItem,
  ADPFilters,
  ADPPlayerRow,
} from '@/types';


type SortColumn =
  | 'overall_adp'
  | 'median_pick'
  | 'min_pick'
  | 'max_pick'
  | 'standard_deviation'
  | 'name'
  | 'position'
  | 'team'
  | 'draft_count'
  | 'selection_rate';

type SortDirection =
  | 'asc'
  | 'desc';

const DRAFT_KIND_LABELS: Record<string, string> = {
  startup: 'Startup',
  rookie: 'Rookie',
  supplemental: 'Supplemental',
};

const QB_FORMAT_LABELS: Record<string, string> = {
  one_qb: '1QB',
  superflex: 'Superflex',
  two_qb: '2QB',
};

const TEP_LABELS: Record<string, string> = {
  none: 'Non-TEP',
  premium: 'TE premium',
};

const SCORING_LABELS: Record<string, string> = {
  standard: 'Standard',
  half_ppr: 'Half PPR',
  ppr: 'PPR',
  custom: 'Custom',
};

function formatDateTime(
  value: string | null,
) {
  if (!value) {
    return '—';
  }

  return new Date(value).toLocaleString();
}


function formatPercent(
  value: number,
) {
  return `${(value * 100).toFixed(1)}%`;
}


function formatDataSource(
  value: string | null | undefined,
) {
  if (value === 'snapshot') {
    return 'Stored snapshot';
  }

  return 'Live aggregate';
}


function buildDynamicOptions(
  rows: ADPDistributionItem[] | undefined,
  {
    allLabel,
    labelMap = {},
    formatLabel,
  }: {
    allLabel: string;
    labelMap?: Record<string, string>;
    formatLabel?: (row: ADPDistributionItem) => string;
  },
) {
  const options = [
    {
      value: '',
      label: allLabel,
    },
  ];

  for (const row of rows ?? []) {
    if (!row.key || row.key === 'unknown') {
      continue;
    }

    const label = formatLabel
      ? formatLabel(row)
      : `${labelMap[row.key] ?? row.key} (${row.count})`;
    options.push({
      value: row.key,
      label,
    });
  }

  return options;
}


function compareRows(
  left: ADPPlayerRow,
  right: ADPPlayerRow,
  column: SortColumn,
  direction: SortDirection,
) {
  const multiplier = direction === 'asc'
    ? 1
    : -1;

  if (column === 'name' || column === 'position' || column === 'team') {
    return multiplier * String(left[column] ?? '').localeCompare(
      String(right[column] ?? ''),
    );
  }

  return multiplier * (
    Number(left[column] ?? Number.NEGATIVE_INFINITY)
    - Number(right[column] ?? Number.NEGATIVE_INFINITY)
  );
}


function getSortIndicator(
  activeColumn: SortColumn,
  activeDirection: SortDirection,
  column: SortColumn,
) {
  if (activeColumn !== column) {
    return null;
  }

  return activeDirection === 'asc'
    ? ' ↑'
    : ' ↓';
}


export const AdpPage = () => {
  const [filters, setFilters] = useState<ADPFilters>({
    season: '2026',
    draft_kind: 'startup',
    qb_format: 'superflex',
    te_premium: '',
    scoring_format: '',
    team_count: 12,
    minimum_draft_count: 1,
    limit: 300,
  });
  const [sortColumn, setSortColumn] = useState<SortColumn>('overall_adp');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const deferredFilters = useDeferredValue(filters);
  const query = useAdp(deferredFilters);
  const metadataQuery = useAdpMetadata(deferredFilters);

  const sortedPlayers = useMemo(() => {
    const players = [...(query.data?.players ?? [])];
    players.sort((left, right) => {
      const value = compareRows(
        left,
        right,
        sortColumn,
        sortDirection,
      );

      if (value !== 0) {
        return value;
      }

      return left.name.localeCompare(right.name);
    });
    return players;
  }, [
    query.data?.players,
    sortColumn,
    sortDirection,
  ]);

  const updateSort = (
    column: SortColumn,
  ) => {
    setSortColumn(column);
    setSortDirection((current) => (
      sortColumn === column && current === 'asc'
        ? 'desc'
        : 'asc'
    ));
  };

  const seasonOptions = useMemo(() => buildDynamicOptions(
    metadataQuery.data?.season_options,
    {
      allLabel: 'All seasons',
      formatLabel: (row) => `${row.key} (${row.count})`,
    },
  ), [metadataQuery.data?.season_options]);

  const draftKindOptions = useMemo(() => buildDynamicOptions(
    metadataQuery.data?.draft_kind_options,
    {
      allLabel: 'All drafts',
      labelMap: DRAFT_KIND_LABELS,
    },
  ), [metadataQuery.data?.draft_kind_options]);

  const qbFormatOptions = useMemo(() => buildDynamicOptions(
    metadataQuery.data?.qb_format_options,
    {
      allLabel: 'All QB formats',
      labelMap: QB_FORMAT_LABELS,
    },
  ), [metadataQuery.data?.qb_format_options]);

  const tepOptions = useMemo(() => buildDynamicOptions(
    metadataQuery.data?.te_premium_options,
    {
      allLabel: 'All TE formats',
      labelMap: TEP_LABELS,
    },
  ), [metadataQuery.data?.te_premium_options]);

  const scoringOptions = useMemo(() => buildDynamicOptions(
    metadataQuery.data?.scoring_format_options,
    {
      allLabel: 'All scoring',
      labelMap: SCORING_LABELS,
    },
  ), [metadataQuery.data?.scoring_format_options]);

  const teamCountOptions = useMemo(() => buildDynamicOptions(
    metadataQuery.data?.team_count_options,
    {
      allLabel: 'Any team count',
      formatLabel: (row) => `${row.key} teams (${row.count})`,
    },
  ), [metadataQuery.data?.team_count_options]);

  return (
    <div className="adp-page">
      <section className="page-hero adp-hero">
        <div>
          <p className="page-eyebrow">Rankings</p>
          <h1>Sleeper ADP board</h1>
          <p className="page-subtitle">
            Aggregated qualified Sleeper drafts, segmented for dynasty formats and served from your local corpus.
          </p>
        </div>
        <div className="adp-hero-note">
          <Database size={18} />
          <span>Public read-only ADP, cached from qualified drafts.</span>
        </div>
      </section>

      <section className="adp-filters-card">
        <div className="adp-filters-header">
          <div>
            <span className="adp-section-kicker">Filters</span>
            <h2>Draft sample controls</h2>
          </div>
          <div className="adp-filters-note">
            <Filter size={16} />
            <span>Changing filters requeries the cached `/adp` dataset.</span>
          </div>
        </div>

        <div className="adp-filters-grid">
          <label>
            <span>Season</span>
            <select
              value={filters.season ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  season: event.target.value.trim() || null,
                }));
              }}
            >
              {seasonOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Draft kind</span>
            <select
              value={filters.draft_kind ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  draft_kind: event.target.value || null,
                }));
              }}
            >
              {draftKindOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>QB format</span>
            <select
              value={filters.qb_format ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  qb_format: event.target.value || null,
                }));
              }}
            >
              {qbFormatOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>TE premium</span>
            <select
              value={filters.te_premium ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  te_premium: event.target.value || null,
                }));
              }}
            >
              {tepOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Scoring</span>
            <select
              value={filters.scoring_format ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  scoring_format: event.target.value || null,
                }));
              }}
            >
              {scoringOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Team count</span>
            <select
              value={filters.team_count?.toString() ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  team_count: event.target.value
                    ? Number(event.target.value)
                    : null,
                }));
              }}
            >
              {teamCountOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Min draft count</span>
            <input
              type="number"
              min={1}
              max={999}
              value={filters.minimum_draft_count ?? 1}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  minimum_draft_count: Number(event.target.value),
                }));
              }}
            />
          </label>

          <label>
            <span>Start date</span>
            <input
              type="date"
              value={filters.start_date ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  start_date: event.target.value || null,
                }));
              }}
            />
          </label>

          <label>
            <span>End date</span>
            <input
              type="date"
              value={filters.end_date ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  end_date: event.target.value || null,
                }));
              }}
            />
          </label>

          <label>
            <span>Rows</span>
            <select
              value={filters.limit?.toString() ?? '300'}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  limit: Number(event.target.value),
                }));
              }}
            >
              {[100, 300, 500, 1000].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {query.isLoading ? (
        <LoadingState label="Loading ADP board" />
      ) : (
        <>
          <section className="adp-summary-grid">
            <article className="adp-summary-card">
              <span>Qualified drafts</span>
              <strong>{query.data?.sample.draft_count.toLocaleString() ?? '0'}</strong>
            </article>
            <article className="adp-summary-card">
              <span>Qualified picks</span>
              <strong>{query.data?.sample.pick_count.toLocaleString() ?? '0'}</strong>
            </article>
            <article className="adp-summary-card">
              <span>Earliest draft</span>
              <strong>{formatDateTime(query.data?.sample.earliest_draft_at ?? null)}</strong>
            </article>
            <article className="adp-summary-card">
              <span>Latest draft</span>
              <strong>{formatDateTime(query.data?.sample.latest_draft_at ?? null)}</strong>
            </article>
            <article className="adp-summary-card">
              <span>Board source</span>
              <strong>{formatDataSource(query.data?.sample.data_source)}</strong>
            </article>
          </section>

          <section className="adp-bias-note">
            <span className="adp-section-kicker">Sample note</span>
            <p>
              This board reflects drafts discovered through your Sleeper graph, not a random sample of all Sleeper drafts.
              Use the draft count, pick count, and date window to judge how representative each filter slice is.
            </p>
          </section>

          <section className="adp-table-card">
            <div className="adp-table-header">
              <div>
                <span className="adp-section-kicker">Board</span>
                <h2>Player ADP table</h2>
              </div>
              <div className="adp-table-meta">
                <small>
                  {formatDataSource(query.data?.sample.data_source)}
                </small>
                <small>
                  Generated {formatDateTime(query.data?.sample.generated_at ?? null)}
                </small>
              </div>
            </div>

            <div className="adp-table-wrap">
              <table className="adp-table">
                <thead>
                  <tr>
                    <th>
                      <button type="button" onClick={() => updateSort('overall_adp')}>
                        ADP{getSortIndicator(sortColumn, sortDirection, 'overall_adp')}
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => updateSort('name')}>
                        Player{getSortIndicator(sortColumn, sortDirection, 'name')}
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => updateSort('position')}>
                        Pos{getSortIndicator(sortColumn, sortDirection, 'position')}
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => updateSort('team')}>
                        Team{getSortIndicator(sortColumn, sortDirection, 'team')}
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => updateSort('median_pick')}>
                        Median{getSortIndicator(sortColumn, sortDirection, 'median_pick')}
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => updateSort('min_pick')}>
                        Range{getSortIndicator(sortColumn, sortDirection, 'min_pick')}
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => updateSort('standard_deviation')}>
                        Std Dev{getSortIndicator(sortColumn, sortDirection, 'standard_deviation')}
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => updateSort('draft_count')}>
                        Drafts{getSortIndicator(sortColumn, sortDirection, 'draft_count')}
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => updateSort('selection_rate')}>
                        Selection rate{getSortIndicator(sortColumn, sortDirection, 'selection_rate')}
                      </button>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedPlayers.map((player) => (
                    <tr key={player.player_id}>
                      <td>{player.overall_adp.toFixed(2)}</td>
                      <td>{player.name}</td>
                      <td>{player.position ?? '—'}</td>
                      <td>{player.team ?? '—'}</td>
                      <td>{player.median_pick.toFixed(1)}</td>
                      <td>{player.min_pick} - {player.max_pick}</td>
                      <td>{player.standard_deviation?.toFixed(2) ?? '—'}</td>
                      <td>{player.draft_count.toLocaleString()}</td>
                      <td>{formatPercent(player.selection_rate)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {!sortedPlayers.length ? (
              <div className="adp-empty-state">
                No qualified players matched this filter set.
              </div>
            ) : null}
          </section>
        </>
      )}
    </div>
  );
};
