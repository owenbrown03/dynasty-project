import React, {
  useMemo,
  useState,
} from 'react';
import { LayoutGrid, List, Loader2 } from 'lucide-react';

import { Skeleton } from '@/components/feedback/Skeleton';
import { useRookieWarHistory } from '@/hooks/useRookieWarHistory';
import { useLeagueOverview } from '@/hooks/sleeper/useLeagues';
import type { RookieWarHistoryRow } from '@/types';
import { formatNumber } from '@/utils/format';

import './RookieWarHistoryBoard.css';

type ViewMode = 'board' | 'list';

type SortColumn =
  | 'draft_year'
  | 'round'
  | 'round_slot'
  | 'player_id'
  | 'roster_war'
  | 'starter_war';

type SortDirection =
  | 'asc'
  | 'desc';

const SORT_LABELS: Record<SortColumn, string> = {
  draft_year: 'Draft Year',
  round: 'Rd',
  round_slot: 'Pick',
  player_id: 'Player',
  starter_war: 'Starter WAR',
  roster_war: 'Roster WAR',
};

function compareRows(
  left: RookieWarHistoryRow,
  right: RookieWarHistoryRow,
  column: SortColumn,
) {
  switch (column) {
    case 'draft_year':
      return left.draft_year - right.draft_year;
    case 'round':
      return left.round - right.round;
    case 'round_slot':
      return left.round_slot - right.round_slot;
    case 'starter_war':
      return (left.starter_war ?? 0) - (right.starter_war ?? 0);
    case 'roster_war':
      return (left.roster_war ?? 0) - (right.roster_war ?? 0);
    case 'player_id':
    default:
      return left.name.localeCompare(right.name);
  }
}

interface PickSlotSummary {
  round: number;
  slot: number;
  pickLabel: string;
  avgWar: number | null;
  medWar: number | null;
  hitRate: number | null;
  bustRate: number | null;
  byYear: Record<number, RookieWarHistoryRow>;
}

function HistoryTableSkeleton({
  withWar,
}: {
  withWar: boolean;
}) {
  const columns = withWar ? 8 : 6;
  return (
    <div className="rkwh-table-card" role="status" aria-live="polite">
      <div className="rkwh-table-header">
        <Skeleton width={160} variant="title" />
        <Skeleton width={120} variant="text" />
      </div>
      <div className="rkwh-table-scroll">
        <table className="rkwh-table">
          <thead>
            <tr>
              {
                Array.from({ length: columns }).map((_, index) => (
                  <th key={index}><Skeleton width={64} variant="text" /></th>
                ))
              }
            </tr>
          </thead>
          <tbody>
            {
              Array.from({ length: 8 }).map((__, rowIndex) => (
                <tr key={rowIndex}>
                  {
                    Array.from({ length: columns }).map((_, colIndex) => (
                      <td key={colIndex}><Skeleton width={52} variant="text" /></td>
                    ))
                  }
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function RookieWarHistoryBoard() {
  const leagueOverview = useLeagueOverview();
  const [leagueId, setLeagueId] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('board');
  const [selectedRound, setSelectedRound] = useState<number | 'all'>('all');
  const [metric, setMetric] = useState<'starter_war' | 'roster_war'>('starter_war');
  const [sort, setSort] = useState<{ column: SortColumn; direction: SortDirection }>({
    column: 'draft_year',
    direction: 'asc',
  });
  const history = useRookieWarHistory(
    leagueId || undefined,
    true,
  );

  const selectedLeagueName = useMemo(
    () => leagueOverview.data.find(
      (league) => league.league_id === leagueId,
    )?.league_name ?? null,
    [leagueId, leagueOverview.data],
  );

  const rows = useMemo(
    () => history.data?.rows ?? [],
    [history.data],
  );
  const hasWar = Boolean(history.data?.has_war);

  // Extract unique sorted years
  const years = useMemo(() => {
    const set = new Set<number>();
    for (const r of rows) {
      if (r.draft_year) {
        set.add(r.draft_year);
      }
    }
    return Array.from(set).sort((a, b) => a - b);
  }, [rows]);

  // Build 48 pick slots (Rounds 1-4, Slots 1-12) with round filter
  const pickSlotSummaries = useMemo<PickSlotSummary[]>(() => {
    const map = new Map<string, RookieWarHistoryRow>();
    for (const r of rows) {
      map.set(`${r.draft_year}-${r.round}-${r.round_slot}`, r);
    }

    const summaries: PickSlotSummary[] = [];
    const targetRounds = selectedRound === 'all' ? [1, 2, 3, 4] : [selectedRound];

    for (const rnd of targetRounds) {
      for (let sl = 1; sl <= 12; sl += 1) {
        const pickLabel = `${rnd}.${sl.toString().padStart(2, '0')}`;
        const byYear: Record<number, RookieWarHistoryRow> = {};
        const wars: number[] = [];

        for (const yr of years) {
          const row = map.get(`${yr}-${rnd}-${sl}`);
          if (row) {
            byYear[yr] = row;
            const warVal = metric === 'starter_war' ? row.starter_war : row.roster_war;
            if (warVal != null) {
              wars.push(warVal);
            }
          }
        }

        let avgWar: number | null = null;
        let medWar: number | null = null;
        let hitRate: number | null = null;
        let bustRate: number | null = null;

        if (wars.length > 0) {
          const sum = wars.reduce((acc, v) => acc + v, 0);
          avgWar = sum / wars.length;
          const sortedWars = [...wars].sort((a, b) => a - b);
          const mid = Math.floor(sortedWars.length / 2);
          medWar = sortedWars.length % 2 !== 0
            ? sortedWars[mid]
            : (sortedWars[mid - 1] + sortedWars[mid]) / 2;

          const hits = wars.filter((v) => v >= 3.0).length;
          const busts = wars.filter((v) => v <= 1.0).length;
          hitRate = (hits / wars.length) * 100;
          bustRate = (busts / wars.length) * 100;
        }

        summaries.push({
          round: rnd,
          slot: sl,
          pickLabel,
          avgWar,
          medWar,
          hitRate,
          bustRate,
          byYear,
        });
      }
    }

    return summaries;
  }, [rows, years, selectedRound, metric]);

  const sortedRows = useMemo(() => {
    const next = [...rows];
    next.sort((left, right) => {
      const value = compareRows(left, right, sort.column);
      if (value !== 0) {
        return sort.direction === 'asc' ? value : -value;
      }
      return left.draft_year - right.draft_year;
    });
    return next;
  }, [rows, sort]);

  const toggleSort = (column: SortColumn) => {
    setSort((current) => (
      current.column === column
        ? { column, direction: current.direction === 'asc' ? 'desc' : 'asc' }
        : { column, direction: 'asc' }
    ));
  };

  const isLoading = history.isLoading;
  const isFetching = history.isFetching;

  const renderWarCell = (value: number | null) => {
    if (!hasWar) {
      return <span className="rkwh-cell-empty">—</span>;
    }
    if (value == null) {
      return <span className="rkwh-cell-empty">—</span>;
    }
    const tone = value > 0 ? 'positive' : (value < 0 ? 'negative' : 'neutral');
    return (
      <span className={`rkwh-war rkwh-war--${tone}`}>
        {formatNumber(value)}
      </span>
    );
  };

  return (
    <div className="rkwh-page">
      <section className="rkwh-toolbar">
        <label className="rkwh-selector">
          <span>League (WAR context)</span>
          <select
            value={leagueId}
            onChange={(event) => setLeagueId(event.target.value)}
          >
            <option value="">
              {hasWar ? 'Clear league (show ADP only)' : 'No league — ADP only'}
            </option>
            {
              leagueOverview.data.map((league) => (
                <option key={league.league_id} value={league.league_id}>
                  {league.league_name}
                </option>
              ))
            }
          </select>
        </label>

        <div className="rkwh-toolbar-meta">
          <span className="rkwh-meta-label">Context</span>
          <strong>
            {
              hasWar
                ? selectedLeagueName ?? history.data?.league_name ?? 'Selected league'
                : 'Consensus Rookie ADP'
            }
          </strong>
        </div>

        {hasWar ? (
          <div className="rkwh-toolbar-meta">
            <span className="rkwh-meta-label">Metric</span>
            <div className="rkwh-pill-group">
              <button
                type="button"
                className={`rkwh-filter-pill ${metric === 'starter_war' ? 'rkwh-filter-pill--active' : ''}`}
                onClick={() => setMetric('starter_war')}
              >
                Starter WAR
              </button>
              <button
                type="button"
                className={`rkwh-filter-pill ${metric === 'roster_war' ? 'rkwh-filter-pill--active' : ''}`}
                onClick={() => setMetric('roster_war')}
              >
                Roster WAR
              </button>
            </div>
          </div>
        ) : null}

        <div className="rkwh-toolbar-meta">
          <span className="rkwh-meta-label">Rounds</span>
          <div className="rkwh-pill-group">
            <button
              type="button"
              className={`rkwh-filter-pill ${selectedRound === 'all' ? 'rkwh-filter-pill--active' : ''}`}
              onClick={() => setSelectedRound('all')}
            >
              All (48)
            </button>
            {[1, 2, 3, 4].map((rnd) => (
              <button
                key={rnd}
                type="button"
                className={`rkwh-filter-pill ${selectedRound === rnd ? 'rkwh-filter-pill--active' : ''}`}
                onClick={() => setSelectedRound(rnd)}
              >
                Rd {rnd}
              </button>
            ))}
          </div>
        </div>

        <div className="rkwh-view-mode-toggle" role="group" aria-label="View mode">
          <button
            type="button"
            className={`rkwh-toggle-btn ${viewMode === 'board' ? 'rkwh-toggle-btn--active' : ''}`}
            onClick={() => setViewMode('board')}
          >
            <LayoutGrid size={14} />
            Board
          </button>
          <button
            type="button"
            className={`rkwh-toggle-btn ${viewMode === 'list' ? 'rkwh-toggle-btn--active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            <List size={14} />
            List
          </button>
        </div>
      </section>

      {
        !hasWar && !isLoading ? (
          <div className="rkwh-hint">
            This board shows historical consensus rookie draft selections.
            Select a league above to compute each player's career <strong>starter</strong> and <strong>roster</strong>{' '}
            WAR under that league's custom scoring settings.
          </div>
        ) : null
      }

      {
        isFetching && !isLoading ? (
          <div className="rkwh-refreshing">
            <Loader2 size={14} className="rkwh-spin" />
            Updating WAR...
          </div>
        ) : null
      }

      {
        isLoading && !history.data
          ? <HistoryTableSkeleton withWar={hasWar} />
          : (
            <div className="rkwh-table-card">
              <div className="rkwh-table-header">
                <div className="rkwh-table-header-title">
                  <strong>Rookie Pick WAR History Board</strong>
                  <small>
                    {hasWar
                      ? `Career ${metric === 'starter_war' ? 'Starter' : 'Roster'} WAR under ${selectedLeagueName ?? 'selected league'}`
                      : 'Consensus draft selections across historical rookie classes'}
                  </small>
                </div>
              </div>

              {viewMode === 'board' ? (
                <div className="rkwh-table-scroll">
                  <table className="rkwh-table rkwh-board-matrix">
                    <thead>
                      <tr className="rkwh-head-row-top">
                        <th className="rkwh-freeze-col rkwh-col-pick" rowSpan={hasWar ? 2 : 1}>Pick</th>
                        {hasWar ? (
                          <>
                            <th className="rkwh-freeze-col rkwh-col-avg" rowSpan={2}>Avg</th>
                            <th className="rkwh-freeze-col rkwh-col-med" rowSpan={2}>Med</th>
                            <th className="rkwh-freeze-col rkwh-col-hit" rowSpan={2}>Hit</th>
                            <th className="rkwh-freeze-col rkwh-col-bust" rowSpan={2}>Bust</th>
                          </>
                        ) : null}
                        {years.map((year) => (
                          <th
                            key={year}
                            colSpan={hasWar ? 2 : 1}
                            className="rkwh-th-year-group"
                          >
                            {year}
                          </th>
                        ))}
                      </tr>
                      {hasWar ? (
                        <tr className="rkwh-head-row-sub">
                          {years.map((year) => (
                            <React.Fragment key={year}>
                              <th className="rkwh-th-sub-player">Player</th>
                              <th className="rkwh-th-sub-war">WAR</th>
                            </React.Fragment>
                          ))}
                        </tr>
                      ) : null}
                    </thead>
                    <tbody>
                      {pickSlotSummaries.map((summary) => (
                        <tr key={summary.pickLabel}>
                          <td className="rkwh-freeze-col rkwh-col-pick rkwh-pick-label">
                            {summary.pickLabel}
                          </td>
                          {hasWar ? (
                            <>
                              <td className="rkwh-freeze-col rkwh-col-avg rkwh-stat-num">
                                {summary.avgWar != null ? formatNumber(summary.avgWar) : '—'}
                              </td>
                              <td className="rkwh-freeze-col rkwh-col-med rkwh-stat-num">
                                {summary.medWar != null ? formatNumber(summary.medWar) : '—'}
                              </td>
                              <td className="rkwh-freeze-col rkwh-col-hit rkwh-stat-num">
                                {summary.hitRate != null ? (
                                  <span className={`rkwh-rate-pill ${summary.hitRate >= 60 ? 'rkwh-rate-pill--good' : ''}`}>
                                    {Math.round(summary.hitRate)}%
                                  </span>
                                ) : '—'}
                              </td>
                              <td className="rkwh-freeze-col rkwh-col-bust rkwh-stat-num">
                                {summary.bustRate != null ? (
                                  <span className={`rkwh-rate-pill ${summary.bustRate >= 50 ? 'rkwh-rate-pill--bad' : ''}`}>
                                    {Math.round(summary.bustRate)}%
                                  </span>
                                ) : '—'}
                              </td>
                            </>
                          ) : null}
                          {years.map((year) => {
                            const p = summary.byYear[year];
                            if (!p) {
                              return (
                                <React.Fragment key={year}>
                                  <td className="rkwh-matrix-cell rkwh-matrix-cell--empty" colSpan={hasWar ? 2 : 1}>
                                    —
                                  </td>
                                </React.Fragment>
                              );
                            }
                            const pos = p.position ?? '??';
                            const warVal = metric === 'starter_war' ? p.starter_war : p.roster_war;
                            return (
                              <React.Fragment key={year}>
                                <td className={`rkwh-matrix-cell rkwh-player-box-cell rkwh-pos-bg--${pos.toLowerCase()}`}>
                                  <div className="rkwh-player-box">
                                    <span className={`rkwh-pos-tag rkwh-pos-tag--${pos.toLowerCase()}`}>
                                      {pos}
                                    </span>
                                    <span className="rkwh-player-name-text" title={p.name}>
                                      {p.name}
                                    </span>
                                  </div>
                                </td>
                                {hasWar ? (
                                  <td className={`rkwh-matrix-cell rkwh-war-val-cell rkwh-pos-bg--${pos.toLowerCase()}`}>
                                    {warVal != null ? (
                                      <span className={`rkwh-war-score ${warVal >= 3.0 ? 'rkwh-war-score--hit' : (warVal <= 1.0 ? 'rkwh-war-score--bust' : '')}`}>
                                        {formatNumber(warVal)}
                                      </span>
                                    ) : '—'}
                                  </td>
                                ) : null}
                              </React.Fragment>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="rkwh-table-scroll">
                  <table className="rkwh-table">
                    <thead>
                      <tr>
                        {(Object.keys(SORT_LABELS) as SortColumn[]).map((column) => (
                          <th
                            key={column}
                            className={column === 'player_id' ? 'rkwh-th-left' : ''}
                          >
                            <button
                              type="button"
                              className="rkwh-th-button"
                              onClick={() => toggleSort(column)}
                            >
                              {SORT_LABELS[column]}
                              {sort.column === column && (
                                <span className="rkwh-sort-arrow">
                                  {sort.direction === 'asc' ? ' ↑' : ' ↓'}
                                </span>
                              )}
                            </button>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sortedRows.map((row) => (
                        <tr key={`${row.draft_year}-${row.round}-${row.round_slot}-${row.player_id}`}>
                          <td className="rkwh-center">{row.draft_year}</td>
                          <td className="rkwh-center">{row.round}</td>
                          <td className="rkwh-center">
                            {row.round}.{row.round_slot.toString().padStart(2, '0')}
                          </td>
                          <td className="rkwh-player-cell">
                            <span
                              className={`rkwh-pos-tag rkwh-pos-tag--${(row.position ?? '??').toLowerCase()}`}
                            >
                              {row.position ?? '??'}
                            </span>
                            <span className="rkwh-player-name-text">{row.name}</span>
                            {row.team && (
                              <span className="rkwh-player-team">({row.team})</span>
                            )}
                          </td>
                          <td className="rkwh-right">{renderWarCell(row.starter_war)}</td>
                          <td className="rkwh-right">{renderWarCell(row.roster_war)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )
      }
    </div>
  );
}
