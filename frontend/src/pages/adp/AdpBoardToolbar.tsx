import {
  BOARD_SORT_OPTIONS,
  DRAFT_ORDER_LABELS,
  type DraftOrderMode,
  type SortColumn,
  type SortDirection,
  type ViewMode,
} from './adp.utils';

interface AdpBoardToolbarProps {
  playerSearch: string;
  positionFilter: string;
  positionOptions: string[];
  viewMode: ViewMode;
  draftOrderMode: DraftOrderMode;
  sortColumn: SortColumn;
  sortDirection: SortDirection;
  visibleCount: number;
  secondaryCount: number;
  onPlayerSearchChange: (value: string) => void;
  onPositionFilterChange: (value: string) => void;
  onViewModeChange: (value: ViewMode) => void;
  onDraftOrderModeChange: (value: DraftOrderMode) => void;
  onSortColumnChange: (value: SortColumn) => void;
  onSortDirectionChange: (value: SortDirection) => void;
}

export function AdpBoardToolbar({
  playerSearch,
  positionFilter,
  positionOptions,
  viewMode,
  draftOrderMode,
  sortColumn,
  sortDirection,
  visibleCount,
  secondaryCount,
  onPlayerSearchChange,
  onPositionFilterChange,
  onViewModeChange,
  onDraftOrderModeChange,
  onSortColumnChange,
  onSortDirectionChange,
}: AdpBoardToolbarProps) {
  return (
    <div className="adp-table-tools">
      <label>
        <span>Search players</span>
        <input
          type="search"
          value={playerSearch}
          placeholder="Search by player, team, or position"
          onChange={(event) => {
            onPlayerSearchChange(event.target.value);
          }}
        />
      </label>

      <label>
        <span>Position</span>
        <select
          value={positionFilter}
          onChange={(event) => {
            onPositionFilterChange(event.target.value);
          }}
        >
          <option value="">All positions</option>
          {positionOptions.map((position) => (
            <option key={position} value={position}>
              {position}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Layout</span>
        <select
          value={viewMode}
          onChange={(event) => {
            onViewModeChange(event.target.value as ViewMode);
          }}
        >
          <option value="board">Board style</option>
          <option value="table">Table style</option>
        </select>
      </label>

      <label>
        <span>Draft order</span>
        <select
          value={draftOrderMode}
          onChange={(event) => {
            onDraftOrderModeChange(event.target.value as DraftOrderMode);
          }}
        >
          {Object.entries(DRAFT_ORDER_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Board order</span>
        <select
          value={sortColumn}
          onChange={(event) => {
            onSortColumnChange(event.target.value as SortColumn);
          }}
        >
          {BOARD_SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Direction</span>
        <select
          value={sortDirection}
          onChange={(event) => {
            onSortDirectionChange(event.target.value as SortDirection);
          }}
        >
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>
      </label>

      <div className="adp-table-tools-summary">
        <span>
          {viewMode === 'board'
            ? 'Visible players / board size'
            : 'Visible / fetched rows'}
        </span>
        <strong>
          {visibleCount.toLocaleString()}
          {' / '}
          {secondaryCount.toLocaleString()}
        </strong>
      </div>
    </div>
  );
}
