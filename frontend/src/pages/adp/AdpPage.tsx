import './AdpPage.css';

import { useDeferredValue, useMemo, useState } from 'react';
import { Database, Filter } from 'lucide-react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useAdp } from '@/hooks/useAdp';
import type {
  ADPFilters,
  ADPPlayerRow,
} from '@/types';


type SortColumn =
  | 'overall_adp'
  | 'median_pick'
  | 'name'
  | 'position'
  | 'team'
  | 'draft_count'
  | 'selection_rate';

type SortDirection =
  | 'asc'
  | 'desc';

const DRAFT_KIND_OPTIONS = [
  { value: '', label: 'All drafts' },
  { value: 'startup', label: 'Startup' },
  { value: 'rookie', label: 'Rookie' },
  { value: 'supplemental', label: 'Supplemental' },
];

const QB_FORMAT_OPTIONS = [
  { value: '', label: 'All QB formats' },
  { value: 'one_qb', label: '1QB' },
  { value: 'superflex', label: 'Superflex' },
  { value: 'two_qb', label: '2QB' },
];

const TEP_OPTIONS = [
  { value: '', label: 'All TE formats' },
  { value: 'none', label: 'Non-TEP' },
  { value: 'premium', label: 'TE premium' },
];

const SCORING_OPTIONS = [
  { value: '', label: 'All scoring' },
  { value: 'standard', label: 'Standard' },
  { value: 'half_ppr', label: 'Half PPR' },
  { value: 'ppr', label: 'PPR' },
  { value: 'custom', label: 'Custom' },
];

const TEAM_COUNT_OPTIONS = [
  { value: '', label: 'Any team count' },
  { value: '10', label: '10 teams' },
  { value: '12', label: '12 teams' },
];

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
            <input
              value={filters.season ?? ''}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  season: event.target.value.trim() || null,
                }));
              }}
              placeholder="2026"
            />
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
              {DRAFT_KIND_OPTIONS.map((option) => (
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
              {QB_FORMAT_OPTIONS.map((option) => (
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
              {TEP_OPTIONS.map((option) => (
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
              {SCORING_OPTIONS.map((option) => (
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
              {TEAM_COUNT_OPTIONS.map((option) => (
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
              <small>
                Generated {formatDateTime(query.data?.sample.generated_at ?? null)}
              </small>
            </div>

            <div className="adp-table-wrap">
              <table className="adp-table">
                <thead>
                  <tr>
                    <th>
                      <button type="button" onClick={() => {
                        setSortColumn('overall_adp');
                        setSortDirection((current) => (
                          sortColumn === 'overall_adp' && current === 'asc'
                            ? 'desc'
                            : 'asc'
                        ));
                      }}
                      >
                        ADP
                      </button>
                    </th>
                    <th>
                      <button type="button" onClick={() => {
                        setSortColumn('name');
                        setSortDirection((current) => (
                          sortColumn === 'name' && current === 'asc'
                            ? 'desc'
                            : 'asc'
                        ));
                      }}
                      >
                        Player
                      </button>
                    </th>
                    <th>Pos</th>
                    <th>Team</th>
                    <th>Median</th>
                    <th>Range</th>
                    <th>Std Dev</th>
                    <th>Drafts</th>
                    <th>Selection rate</th>
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
