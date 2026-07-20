import { LoadingState } from '@/components/feedback/LoadingState';
import { Skeleton } from '@/components/feedback/Skeleton';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type { PersonalValuePoolItem } from '@/types';
import { getPositionColor } from '@/utils/positions';

import {
  SORT_LABELS,
  formatMarketNumber,
  formatMetric,
  type FilterColumn,
  type FilterOperator,
  type SortColumn,
  type SortDirection,
  type TableFilter,
} from './myValues.utils';

const MY_VALUES_TABLE_COLUMNS = [
  'Player',
  'Pos',
  'Team',
  'UD Rank',
  'KTC',
  'FC',
  'ADP',
  'Market D Ro',
  'My D Ro',
  'Delta',
];

function MyValuesPoolSkeleton() {
  return (
    <div className="my-values-table-wrap" role="status" aria-live="polite">
      <span className="skeleton-sr-label">Building personal value pool...</span>
      <table className="my-values-table my-values-table-skeleton">
        <thead>
          <tr>
            {
              MY_VALUES_TABLE_COLUMNS.map((column) => (
                <th key={column}>{column}</th>
              ))
            }
          </tr>
        </thead>
        <tbody>
          {
            Array.from({ length: 12 }).map((_, rowIndex) => (
              <tr key={rowIndex}>
                <td>
                  <div className="my-values-table-player">
                    <Skeleton width={34} height={34} radius={4} />
                    <div>
                      <Skeleton width={150} variant="title" />
                      <Skeleton width={90} variant="text" />
                    </div>
                  </div>
                </td>
                {
                  Array.from({ length: MY_VALUES_TABLE_COLUMNS.length - 1 }).map((__, columnIndex) => (
                    <td key={columnIndex}>
                      <Skeleton width={columnIndex < 3 ? 46 : 72} height={16} />
                    </td>
                  ))
                }
              </tr>
            ))
          }
        </tbody>
      </table>
    </div>
  );
}

interface MyValuesPoolPanelProps {
  leagueName: string;
  fetching: boolean;
  loading: boolean;
  searchSort: SortColumn;
  sortDirection: SortDirection;
  tableFilters: TableFilter[];
  filteredPoolItems: PersonalValuePoolItem[];
  filteredPoolCount: number;
  pageSummaryMetric: string;
  selectedPlayerId: string;
  onSearchSortChange: (value: SortColumn) => void;
  onSortDirectionChange: (value: SortDirection) => void;
  onAddTableFilter: () => void;
  onUpdateTableFilter: (
    id: number,
    updates: Partial<TableFilter>,
  ) => void;
  onRemoveTableFilter: (id: number) => void;
  onHeaderSort: (column: SortColumn) => void;
  onSelectPlayer: (playerId: string) => void;
}

export function MyValuesPoolPanel({
  leagueName,
  fetching,
  loading,
  searchSort,
  sortDirection,
  tableFilters,
  filteredPoolItems,
  filteredPoolCount,
  pageSummaryMetric,
  selectedPlayerId,
  onSearchSortChange,
  onSortDirectionChange,
  onAddTableFilter,
  onUpdateTableFilter,
  onRemoveTableFilter,
  onHeaderSort,
  onSelectPlayer,
}: MyValuesPoolPanelProps) {
  return (
    <aside className="my-values-pool-panel">
      <div className="my-values-panel-header">
        <div>
          <p>Projection pool</p>
          <h2>{leagueName}</h2>
        </div>
        {
          fetching
            ? (
              <LoadingState
                inline
                label="Refreshing"
              />
            )
            : null
        }
      </div>

      <div className="my-values-pool-note">
        This is the main projection sheet. It starts with every underdog-ranked player, then keeps any extra players you save custom projections for.
      </div>

      <div className="my-values-pool-toolbar">
        <label className="my-values-control">
          <span>Sort table by</span>
          <select
            value={searchSort}
            onChange={(event) => {
              onSearchSortChange(
                event.target.value as SortColumn,
              );
            }}
          >
            {
              Object.entries(SORT_LABELS).map(([value, label]) => (
                <option
                  key={value}
                  value={value}
                >
                  {label}
                </option>
              ))
            }
          </select>
        </label>

        <label className="my-values-control">
          <span>Direction</span>
          <select
            value={sortDirection}
            onChange={(event) => {
              onSortDirectionChange(
                event.target.value as SortDirection,
              );
            }}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
      </div>

      <div className="my-values-filter-stack">
        <div className="my-values-filter-header">
          <span>Table filters</span>
          <button
            type="button"
            className="button-secondary"
            onClick={onAddTableFilter}
          >
            Add filter
          </button>
        </div>

        {
          tableFilters.map((filter) => (
            <div
              key={filter.id}
              className="my-values-filter-row"
            >
              <select
                value={filter.column}
                onChange={(event) => {
                  onUpdateTableFilter(
                    filter.id,
                    {
                      column: event.target.value as FilterColumn,
                    },
                  );
                }}
              >
                {
                  Object.entries(SORT_LABELS).map(([value, label]) => (
                    <option
                      key={value}
                      value={value}
                    >
                      {label}
                    </option>
                  ))
                }
              </select>

              <select
                value={filter.operator}
                onChange={(event) => {
                  onUpdateTableFilter(
                    filter.id,
                    {
                      operator: event.target.value as FilterOperator,
                    },
                  );
                }}
              >
                <option value="contains">contains</option>
                <option value="equals">equals</option>
                <option value="gt">greater than</option>
                <option value="lt">less than</option>
              </select>

              <input
                value={filter.value}
                placeholder="Filter value"
                onChange={(event) => {
                  onUpdateTableFilter(
                    filter.id,
                    {
                      value: event.target.value,
                    },
                  );
                }}
              />

              <button
                type="button"
                className="button-secondary"
                onClick={() => {
                  onRemoveTableFilter(filter.id);
                }}
              >
                Remove
              </button>
            </div>
          ))
        }
      </div>

      <div className="my-values-pool-summary">
        Showing {filteredPoolCount} players, position-grouped in one sheet and sorted by {pageSummaryMetric}.
      </div>

      {
        loading
          ? (
            <MyValuesPoolSkeleton />
          )
          : null
      }

      {
        !loading
          ? (
            <div className="my-values-table-wrap">
              <table className="my-values-table">
                <thead>
                  <tr>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('player'); }}>Player</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('position'); }}>Pos</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('team'); }}>Team</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('underdog_rank'); }}>UD Rank</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('ktc'); }}>KTC</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('fantasycalc'); }}>FC</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('adp'); }}>ADP</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('market_war'); }}>Market D Ro</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('my_war'); }}>My D Ro</button></th>
                    <th><button type="button" className="my-values-th-button" onClick={() => { onHeaderSort('delta'); }}>Delta</button></th>
                  </tr>
                </thead>
                <tbody>
                  {
                    filteredPoolItems.map((item) => (
                      <tr
                        key={item.player.player_id}
                        className={
                          selectedPlayerId === item.player.player_id
                            ? 'selected'
                            : ''
                        }
                        onClick={() => {
                          onSelectPlayer(
                            item.player.player_id,
                          );
                        }}
                      >
                        <td>
                          <div className="my-values-table-player">
                            <PlayerAvatar
                              playerId={item.player.player_id}
                              name={item.player.name}
                              size="sm"
                            />
                            <div>
                              <strong>{item.player.name}</strong>
                              <p>
                                {item.is_customized
                                  ? 'Customized'
                                  : 'Underdog default'}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span
                            style={{
                              color: getPositionColor(
                                item.player.position,
                              ),
                              fontWeight: 700,
                            }}
                          >
                            {item.player.position}
                          </span>
                        </td>
                        <td>{item.player.team ?? '--'}</td>
                        <td>{item.player.underdog_position_rank ?? '--'}</td>
                        <td>{formatMarketNumber(item.player.ktc_value)}</td>
                        <td>{formatMarketNumber(item.player.fc_value)}</td>
                        <td>{formatMarketNumber(item.player.adp_value)}</td>
                        <td>{formatMetric(item.market_values.dynasty_roster_war)}</td>
                        <td>{formatMetric(item.custom_values.dynasty_roster_war)}</td>
                        <td>
                          {
                            item.delta_values.dynasty_roster_war == null
                              ? '--'
                              : `${item.delta_values.dynasty_roster_war > 0 ? '+' : ''}${formatMetric(item.delta_values.dynasty_roster_war)}`
                          }
                        </td>
                      </tr>
                    ))
                  }
                </tbody>
              </table>
            </div>
          )
          : null
      }
    </aside>
  );
}
