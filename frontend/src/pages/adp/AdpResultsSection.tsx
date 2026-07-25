import type { ADPPlayerRow } from '@/types';

import { AdpBoard } from './AdpBoard';
import { AdpBoardToolbar } from './AdpBoardToolbar';
import { AdpTable } from './AdpTable';
import {
  formatDataSource,
  formatDateTime,
  type BoardDisplayRows,
  type DraftOrderMode,
  type SortColumn,
  type SortDirection,
  type ViewMode,
} from './adp.utils';

interface AdpResultsSectionProps {
  dataSource?: string | null;
  generatedAt?: string | null;
  playerSearch: string;
  positionFilter: string;
  positionOptions: string[];
  viewMode: ViewMode;
  draftOrderMode: DraftOrderMode;
  sortColumn: SortColumn;
  sortDirection: SortDirection;
  boardPlayers: ADPPlayerRow[];
  sortedPlayers: ADPPlayerRow[];
  totalPlayerCount: number;
  boardSize: number;
  boardDisplayRows: BoardDisplayRows;
  onExportCsv: () => void;
  onPlayerSearchChange: (value: string) => void;
  onPositionFilterChange: (value: string) => void;
  onViewModeChange: (value: ViewMode) => void;
  onDraftOrderModeChange: (value: DraftOrderMode) => void;
  onSortColumnChange: (value: SortColumn) => void;
  onSortDirectionChange: (value: SortDirection) => void;
}

export function AdpResultsSection({
  dataSource,
  generatedAt,
  playerSearch,
  positionFilter,
  positionOptions,
  viewMode,
  draftOrderMode,
  sortColumn,
  sortDirection,
  boardPlayers,
  sortedPlayers,
  totalPlayerCount,
  boardSize,
  boardDisplayRows,
  onExportCsv,
  onPlayerSearchChange,
  onPositionFilterChange,
  onViewModeChange,
  onDraftOrderModeChange,
  onSortColumnChange,
  onSortDirectionChange,
}: AdpResultsSectionProps) {
  const visibleCount = viewMode === 'board'
    ? boardPlayers.length
    : sortedPlayers.length;
  const secondaryCount = viewMode === 'board'
    ? boardSize
    : totalPlayerCount;

  return (
    <section className="adp-table-card">
      <div className="adp-table-header">
        <div>
          <span className="adp-section-kicker">Board</span>
          <h2>Startup draft board</h2>
        </div>
        <div className="adp-table-meta">
          <button
            type="button"
            className="site-button site-button-secondary"
            onClick={onExportCsv}
          >
            Export CSV
          </button>
          <small>
            {formatDataSource(dataSource)}
          </small>
          <small>
            Generated {formatDateTime(generatedAt ?? null)}
          </small>
        </div>
      </div>

      <AdpBoardToolbar
        playerSearch={playerSearch}
        positionFilter={positionFilter}
        positionOptions={positionOptions}
        viewMode={viewMode}
        draftOrderMode={draftOrderMode}
        sortColumn={sortColumn}
        sortDirection={sortDirection}
        visibleCount={visibleCount}
        secondaryCount={secondaryCount}
        onPlayerSearchChange={onPlayerSearchChange}
        onPositionFilterChange={onPositionFilterChange}
        onViewModeChange={onViewModeChange}
        onDraftOrderModeChange={onDraftOrderModeChange}
        onSortColumnChange={onSortColumnChange}
        onSortDirectionChange={onSortDirectionChange}
      />

      {viewMode === 'board' ? (
        <AdpBoard
          boardDisplayRows={boardDisplayRows}
          boardSize={boardSize}
          draftOrderMode={draftOrderMode}
        />
      ) : (
        <AdpTable players={sortedPlayers} />
      )}

      {!visibleCount ? (
        <div className="adp-empty-state">
          No qualified players matched this filter set.
        </div>
      ) : null}
    </section>
  );
}
