import {
  useMemo,
  useState,
} from 'react';
import { Loader2 } from 'lucide-react';

import { Skeleton } from '@/components/feedback/Skeleton';
import { useRookieWarHistory } from '@/hooks/useRookieWarHistory';
import { useLeagueOverview } from '@/hooks/sleeper/useLeagues';
import type { RookieWarHistoryRow } from '@/types';
import { getPositionColor } from '@/utils/positions';
import { formatNumber } from '@/utils/format';

import './RookieWarHistoryBoard.css';

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
                : 'Rookie ADP (preloaded)'
            }
          </strong>
        </div>

        <div className="rkwh-toolbar-meta">
          <span className="rkwh-meta-label">Players</span>
          <strong>
            {isLoading ? '…' : rows.length.toLocaleString()}
          </strong>
        </div>
      </section>

      {
        !hasWar && !isLoading ? (
          <div className="rkwh-hint">
            This board lists every past rookie draft selection used to build the
            Rookie Pick WAR averages. Pick a league above to compute each
            player's career <strong>starter</strong> and <strong>roster</strong>{' '}
            WAR under that league's scoring.
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
                <div>
                  <strong>Rookie pick WAR history</strong>
                  <small>
                    {hasWar
                      ? `Career WAR under ${selectedLeagueName ?? 'selected league'}`
                      : 'Career WAR requires a league selection'}
                  </small>
                </div>
                <div className="rkwh-selector-sort-label">
                  Click a column to sort
                </div>
              </div>

              <div className="rkwh-table-scroll">
                <table className="rkwh-table">
                  <thead>
                    <tr>
                      {
                        (Object.keys(SORT_LABELS) as SortColumn[]).map((column) => (
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
                              {
                                sort.column === column
                                  ? <span className="rkwh-sort-indicator">{sort.direction === 'asc' ? '▲' : '▼'}</span>
                                  : null
                              }
                            </button>
                          </th>
                        ))
                      }
                    </tr>
                  </thead>
                  <tbody>
                    {
                      sortedRows.length === 0 ? (
                        <tr>
                          <td colSpan={Object.keys(SORT_LABELS).length} className="rkwh-empty">
                            No rookie selections found.
                          </td>
                        </tr>
                      ) : (
                        sortedRows.map((row) => (
                          <tr key={`${row.draft_year}-${row.round}-${row.round_slot}-${row.player_id}`}>
                            <td>{row.draft_year}</td>
                            <td>{row.round}</td>
                            <td>{row.round_slot}</td>
                            <td className="rkwh-player-cell">
                              <span
                                className="rkwh-position-dot"
                                style={{ background: getPositionColor(row.position ?? '') }}
                              />
                              <span className="rkwh-player-name">{row.name}</span>
                            </td>
                            <td>{row.position ?? '—'}</td>
                            <td>{row.team ?? '—'}</td>
                            <td className="rkwh-war-cell">{renderWarCell(row.starter_war)}</td>
                            <td className="rkwh-war-cell">{renderWarCell(row.roster_war)}</td>
                          </tr>
                        ))
                      )
                    }
                  </tbody>
                </table>
              </div>
            </div>
          )
      }
    </div>
  );
}
