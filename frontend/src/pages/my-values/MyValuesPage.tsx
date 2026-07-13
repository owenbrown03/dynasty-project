import './MyValuesPage.css';

import { AxiosError } from 'axios';
import {
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { useValuePreference } from '@/context/useValuePreference';
import { useLeagueOverview } from '@/hooks/sleeper/useLeagues';
import {
  usePersonalValueDetail,
  usePersonalValuePool,
  usePersonalValueSearch,
  useSavePersonalValueDetail,
} from '@/hooks/sleeper/usePersonalValues';
import type {
  PersonalProjectionOutcomeItem,
  PersonalProjectionSeasonItem,
  PersonalValuePoolItem,
  ValueBasis,
} from '@/types';
import { notify } from '@/utils/notify';
import { getPositionColor } from '@/utils/positions';

type SortColumn =
  | 'player'
  | 'team'
  | 'position'
  | 'underdog_rank'
  | 'ktc'
  | 'fantasycalc'
  | 'market_war'
  | 'my_war'
  | 'delta';

type SortDirection =
  | 'asc'
  | 'desc';

type FilterColumn = SortColumn;

type FilterOperator =
  | 'contains'
  | 'equals'
  | 'gt'
  | 'lt';

interface TableFilter {
  id: number;
  column: FilterColumn;
  operator: FilterOperator;
  value: string;
}

const POSITION_ORDER: Record<string, number> = {
  QB: 0,
  RB: 1,
  WR: 2,
  TE: 3,
};

const SORT_LABELS: Record<SortColumn, string> = {
  player: 'Player',
  team: 'Team',
  position: 'Position',
  underdog_rank: 'Underdog rank',
  ktc: 'KTC',
  fantasycalc: 'FantasyCalc',
  market_war: 'Market dynasty roster WAR',
  my_war: 'My dynasty roster WAR',
  delta: 'Delta',
};


function getDefaultSortColumn(
  preference: ValueBasis,
): SortColumn {
  if (preference === 'fantasycalc') {
    return 'fantasycalc';
  }

  if (preference === 'ktc') {
    return 'ktc';
  }

  return 'my_war';
}


function formatMetric(
  value: number | null | undefined,
) {
  if (value == null) {
    return '--';
  }

  return value.toFixed(2);
}


function formatMarketNumber(
  value: number | null | undefined,
) {
  if (value == null) {
    return '--';
  }

  return Math.round(value).toLocaleString();
}


function parseUnderdogRank(
  value: string | null | undefined,
) {
  if (!value) {
    return Number.POSITIVE_INFINITY;
  }

  const match = value.match(/\d+/);
  return match
    ? Number(match[0])
    : Number.POSITIVE_INFINITY;
}


function getItemValueByColumn(
  item: PersonalValuePoolItem,
  column: SortColumn,
) {
  switch (column) {
    case 'player':
      return item.player.name;
    case 'team':
      return item.player.team ?? '';
    case 'position':
      return item.player.position;
    case 'underdog_rank':
      return parseUnderdogRank(
        item.player.underdog_position_rank,
      );
    case 'ktc':
      return item.player.ktc_value ?? Number.NEGATIVE_INFINITY;
    case 'fantasycalc':
      return item.player.fc_value ?? Number.NEGATIVE_INFINITY;
    case 'market_war':
      return item.market_values.dynasty_roster_war ?? Number.NEGATIVE_INFINITY;
    case 'my_war':
      return item.custom_values.dynasty_roster_war ?? Number.NEGATIVE_INFINITY;
    case 'delta':
      return item.delta_values.dynasty_roster_war ?? Number.NEGATIVE_INFINITY;
  }
}


function comparePoolItems(
  left: PersonalValuePoolItem,
  right: PersonalValuePoolItem,
  column: SortColumn,
  direction: SortDirection,
) {
  const positionDiff = (
    (POSITION_ORDER[left.player.position] ?? 99)
    - (POSITION_ORDER[right.player.position] ?? 99)
  );

  if (positionDiff !== 0) {
    return positionDiff;
  }

  const leftValue = getItemValueByColumn(
    left,
    column,
  );
  const rightValue = getItemValueByColumn(
    right,
    column,
  );

  if (
    typeof leftValue === 'string'
    && typeof rightValue === 'string'
  ) {
    const comparison = leftValue.localeCompare(
      rightValue,
    );
    return direction === 'asc'
      ? comparison
      : comparison * -1;
  }

  const numericComparison = (
    Number(leftValue)
    - Number(rightValue)
  );

  if (numericComparison === 0) {
    return left.player.name.localeCompare(
      right.player.name,
    );
  }

  return direction === 'asc'
    ? numericComparison
    : numericComparison * -1;
}


function itemMatchesFilter(
  item: PersonalValuePoolItem,
  filter: TableFilter,
) {
  const rawValue = getItemValueByColumn(
    item,
    filter.column,
  );

  if (
    filter.operator === 'contains'
    || filter.operator === 'equals'
  ) {
    const left = String(rawValue).toLowerCase();
    const right = filter.value.trim().toLowerCase();

    if (!right) {
      return true;
    }

    return filter.operator === 'contains'
      ? left.includes(right)
      : left === right;
  }

  const target = Number(filter.value);

  if (Number.isNaN(target)) {
    return true;
  }

  const numericValue = Number(rawValue);

  if (filter.operator === 'gt') {
    return numericValue > target;
  }

  return numericValue < target;
}


function getErrorMessage(
  error: unknown,
) {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;

    if (typeof detail === 'string') {
      return detail;
    }
  }

  return 'Unable to save personal projections.';
}


function buildEmptyOutcome(): PersonalProjectionOutcomeItem {
  return {
    position_rank: 1,
    probability: 100,
  };
}


function cloneSeasons(
  seasons: PersonalProjectionSeasonItem[],
) {
  return seasons.map((season, index) => {
    const outcomes = season.outcomes.map(
      (outcome) => ({
        ...outcome,
      }),
    );

    if (index === 0 && outcomes.length === 0) {
      outcomes.push({
        position_rank:
          season.default_position_rank ?? 1,
        probability: 100,
      });
    }

    return {
      ...season,
      outcomes,
    };
  });
}


function getPoolPlayerIds(
  poolItems: PersonalValuePoolItem[],
) {
  return new Set(
    poolItems.map((item) => item.player.player_id),
  );
}


function MetricRail({
  label,
  market,
  mine,
  delta,
}: {
  label: string;
  market: number | null | undefined;
  mine: number | null | undefined;
  delta: number | null | undefined;
}) {
  const deltaClassName = (
    delta == null
      ? ''
      : delta > 0
        ? 'positive'
        : delta < 0
          ? 'negative'
          : 'neutral'
  );

  return (
    <div className="my-values-metric-card">
      <span>{label}</span>
      <strong>{formatMetric(mine)}</strong>
      <div className="my-values-metric-meta">
        <p>Market {formatMetric(market)}</p>
        <p className={deltaClassName}>
          Delta {delta == null ? '--' : `${delta > 0 ? '+' : ''}${formatMetric(delta)}`}
        </p>
      </div>
    </div>
  );
}


export const MyValuesPage = () => {
  const valuePreference = useValuePreference();
  const leagueOverview = useLeagueOverview();
  const [leagueId, setLeagueId] = useState('');
  const [selectedPlayerId, setSelectedPlayerId] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchSort, setSearchSort] = useState<SortColumn>(
    getDefaultSortColumn(valuePreference.preference),
  );
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [tableFilters, setTableFilters] = useState<TableFilter[]>([
    {
      id: 1,
      column: 'player',
      operator: 'contains',
      value: '',
    },
  ]);
  const deferredSearchTerm = useDeferredValue(
    searchTerm,
  );

  const pool = usePersonalValuePool(
    leagueId || undefined,
  );
  const detail = usePersonalValueDetail(
    leagueId || undefined,
    selectedPlayerId || undefined,
  );
  const search = usePersonalValueSearch(
    deferredSearchTerm,
    leagueId || undefined,
  );
  const saveProjection = useSavePersonalValueDetail();
  const [editableSeasons, setEditableSeasons] = useState<
    PersonalProjectionSeasonItem[]
  >([]);

  useEffect(() => {
    if (
      !leagueId
      && leagueOverview.data.length > 0
    ) {
      setLeagueId(
        leagueOverview.data[0].league_id,
      );
    }
  }, [
    leagueId,
    leagueOverview.data,
  ]);

  useEffect(() => {
    setSearchSort(
      getDefaultSortColumn(
        valuePreference.preference,
      ),
    );
  }, [valuePreference.preference]);

  useEffect(() => {
    if (detail.data) {
      setEditableSeasons(
        cloneSeasons(detail.data.seasons),
      );
    } else {
      setEditableSeasons([]);
    }
  }, [detail.data]);

  const poolItems = useMemo(
    () =>
      pool.data?.groups.flatMap(
        (group) => group.players,
      ) ?? [],
    [pool.data],
  );

  useEffect(() => {
    if (!poolItems.length) {
      return;
    }

    if (!selectedPlayerId) {
      setSelectedPlayerId(
        poolItems[0].player.player_id,
      );
    }
  }, [
    poolItems,
    selectedPlayerId,
  ]);

  const sortedSearchResults = useMemo(() => {
    const items = [...search.data];

    items.sort((left, right) => {
      const leftMetric = (
        searchSort === 'fantasycalc'
          ? left.fc_value
          : searchSort === 'my_war'
            || searchSort === 'market_war'
            ? left.dynasty_roster_war
            : left.ktc_value
      ) ?? Number.NEGATIVE_INFINITY;
      const rightMetric = (
        searchSort === 'fantasycalc'
          ? right.fc_value
          : searchSort === 'my_war'
            || searchSort === 'market_war'
            ? right.dynasty_roster_war
            : right.ktc_value
      ) ?? Number.NEGATIVE_INFINITY;

      if (rightMetric !== leftMetric) {
        return rightMetric - leftMetric;
      }

      return left.name.localeCompare(
        right.name,
      );
    });

    return items;
  }, [
    search.data,
    searchSort,
  ]);

  const filteredPoolItems = useMemo(() => {
    const activeFilters = tableFilters.filter(
      (filter) => filter.value.trim().length > 0,
    );
    const items = [...poolItems].filter((item) =>
      activeFilters.every((filter) =>
        itemMatchesFilter(
          item,
          filter,
        ),
      ),
    );

    items.sort((left, right) =>
      comparePoolItems(
        left,
        right,
        searchSort,
        sortDirection,
      ),
    );

    return items;
  }, [
    poolItems,
    tableFilters,
    searchSort,
    sortDirection,
  ]);

  const handleOutcomeChange = (
    season: number,
    outcomeIndex: number,
    field: 'position_rank' | 'probability',
    value: number,
  ) => {
    setEditableSeasons((current) =>
      current.map((seasonItem) => {
        if (seasonItem.season !== season) {
          return seasonItem;
        }

        return {
          ...seasonItem,
          outcomes: seasonItem.outcomes.map(
            (outcome, index) =>
              index === outcomeIndex
                ? {
                  ...outcome,
                  [field]: value,
                }
                : outcome,
          ),
        };
      }),
    );
  };

  const handleCurrentRankChange = (
    season: number,
    nextRank: number,
  ) => {
    setEditableSeasons((current) =>
      current.map((seasonItem) => {
        if (seasonItem.season !== season) {
          return seasonItem;
        }

        return {
          ...seasonItem,
          outcomes: [
            {
              position_rank: nextRank,
              probability: 100,
            },
          ],
        };
      }),
    );
  };

  const handleAddOutcome = (
    season: number,
  ) => {
    setEditableSeasons((current) =>
      current.map((seasonItem) => {
        if (seasonItem.season !== season) {
          return seasonItem;
        }

        return {
          ...seasonItem,
          outcomes: [
            ...seasonItem.outcomes,
            buildEmptyOutcome(),
          ],
        };
      }),
    );
  };

  const handleRemoveOutcome = (
    season: number,
    outcomeIndex: number,
  ) => {
    setEditableSeasons((current) =>
      current.map((seasonItem) => {
        if (seasonItem.season !== season) {
          return seasonItem;
        }

        return {
          ...seasonItem,
          outcomes: seasonItem.outcomes.filter(
            (_, index) => index !== outcomeIndex,
          ),
        };
      }),
    );
  };

  const handleReset = () => {
    if (!detail.data) {
      return;
    }

    setEditableSeasons(
      cloneSeasons(detail.data.seasons),
    );
  };

  const handleSave = async () => {
    if (!leagueId || !selectedPlayerId) {
      return;
    }

    try {
      await saveProjection.savePersonalValue({
        leagueId,
        playerId: selectedPlayerId,
        payload: {
          seasons: editableSeasons.map(
            (season) => ({
              season: season.season,
              outcomes: season.outcomes.map(
                (outcome) => ({
                  position_rank: Number(
                    outcome.position_rank,
                  ),
                  probability: Number(
                    outcome.probability,
                  ),
                }),
              ),
            }),
          ),
        },
      });
      notify.success('Personal projections saved.');
    } catch (error) {
      notify.error(
        getErrorMessage(error),
      );
    }
  };

  const addTableFilter = () => {
    setTableFilters((current) => [
      ...current,
      {
        id: Date.now(),
        column: 'player',
        operator: 'contains',
        value: '',
      },
    ]);
  };

  const updateTableFilter = (
    id: number,
    updates: Partial<TableFilter>,
  ) => {
    setTableFilters((current) =>
      current.map((filter) =>
        filter.id === id
          ? {
            ...filter,
            ...updates,
          }
          : filter,
      ),
    );
  };

  const removeTableFilter = (
    id: number,
  ) => {
    setTableFilters((current) =>
      current.length === 1
        ? [
          {
            id: 1,
            column: 'player',
            operator: 'contains',
            value: '',
          },
        ]
        : current.filter((filter) => filter.id !== id),
    );
  };

  const handleHeaderSort = (
    column: SortColumn,
  ) => {
    if (searchSort === column) {
      setSortDirection((current) =>
        current === 'asc'
          ? 'desc'
          : 'asc',
      );
      return;
    }

    setSearchSort(column);
    setSortDirection(
      column === 'player'
        || column === 'team'
        || column === 'position'
          ? 'asc'
          : 'desc',
    );
  };

  const selectedLeagueName = (
    leagueOverview.data.find(
      (league) => league.league_id === leagueId,
    )?.league_name
    ?? 'Select a league'
  );
  const poolPlayerIds = getPoolPlayerIds(
    poolItems,
  );
  const selectedPlayerInPool = poolPlayerIds.has(
    selectedPlayerId,
  );
  const selectedPlayer = detail.data?.player;
  const currentProjectionSeason = (
    detail.data?.context.season
  );
  const marketValues = detail.data?.market_values;
  const customValues = detail.data?.custom_values;
  const deltaValues = detail.data?.delta_values;
  const pageSummaryMetric = (
    searchSort === 'fantasycalc'
      ? 'FantasyCalc'
      : searchSort === 'my_war'
        ? 'My dynasty roster WAR'
        : searchSort === 'market_war'
          ? 'Market dynasty roster WAR'
          : SORT_LABELS[searchSort]
  );
  const filteredPoolCount = filteredPoolItems.length;

  return (
    <div className="my-values-page">
      <section className="my-values-header">
        <div>
          <p className="page-eyebrow">Projections</p>
          <h1 className="my-values-title">
            Personal values
          </h1>
          <p className="my-values-description">
            Start from Underdog rank defaults, layer in your own weighted finish outcomes, and compare market WAR against your custom dynasty view inside a real league context.
          </p>
        </div>

        <div className="my-values-header-controls">
          <label className="my-values-control">
            <span>League context</span>
            <select
              value={leagueId}
              onChange={(event) => {
                setLeagueId(
                  event.target.value,
                );
                setSelectedPlayerId('');
              }}
            >
              {
                leagueOverview.data.map((league) => (
                  <option
                    key={league.league_id}
                    value={league.league_id}
                  >
                    {league.league_name}
                  </option>
                ))
              }
            </select>
          </label>

          <div className="my-values-header-chip">
            <span>Default table sort</span>
            <strong>{pageSummaryMetric}</strong>
          </div>
        </div>
      </section>

      <section className="my-values-workspace">
        <aside className="my-values-pool-panel">
          <div className="my-values-panel-header">
            <div>
              <p>Projection pool</p>
              <h2>{selectedLeagueName}</h2>
            </div>
            {
              pool.fetching
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
                  setSearchSort(
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
                  setSortDirection(
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
                onClick={addTableFilter}
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
                      updateTableFilter(
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
                      updateTableFilter(
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
                      updateTableFilter(
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
                      removeTableFilter(filter.id);
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
            pool.loading
              ? (
                <LoadingState label="Building personal value pool..." />
              )
              : null
          }

          {
            !pool.loading
              ? (
                <div className="my-values-table-wrap">
                  <table className="my-values-table">
                    <thead>
                      <tr>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('player'); }}>Player</button></th>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('position'); }}>Pos</button></th>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('team'); }}>Team</button></th>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('underdog_rank'); }}>UD Rank</button></th>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('ktc'); }}>KTC</button></th>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('fantasycalc'); }}>FC</button></th>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('market_war'); }}>Market D Ro</button></th>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('my_war'); }}>My D Ro</button></th>
                        <th><button type="button" className="my-values-th-button" onClick={() => { handleHeaderSort('delta'); }}>Delta</button></th>
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
                              setSelectedPlayerId(
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

        <section className="my-values-editor-panel">
          <div className="my-values-search-card">
            <div className="my-values-panel-header">
              <div>
                <p>Add players</p>
                <h2>Add players missing from the sheet</h2>
              </div>
            </div>

            <div className="my-values-search-controls">
              <label className="my-values-control my-values-control-grow">
                <span>Player search</span>
                <input
                  value={searchTerm}
                  placeholder="Search player name"
                  onChange={(event) => {
                    setSearchTerm(
                      event.target.value,
                    );
                  }}
                />
              </label>
            </div>

            {
              search.enabled
                ? (
                  <div className="my-values-search-results">
                    {
                      search.loading || search.fetching
                        ? (
                          <LoadingState
                            inline
                            label="Searching"
                          />
                        )
                        : sortedSearchResults.map((result) => (
                          <button
                            key={result.player_id}
                            type="button"
                            className="my-values-search-result"
                            onClick={() => {
                              setSelectedPlayerId(
                                result.player_id,
                              );
                            }}
                          >
                            <div className="my-values-pool-player">
                              <PlayerAvatar
                                playerId={result.player_id}
                                name={result.name}
                                size="sm"
                              />
                              <div>
                                <strong>{result.name}</strong>
                                <p>
                                  {result.position ?? '--'} · {result.team ?? '--'} · {result.underdog_position_rank ?? 'No UD rank'}
                                </p>
                              </div>
                            </div>

                            <div className="my-values-search-metrics">
                              <span>KTC {result.ktc_value?.toLocaleString() ?? '--'}</span>
                              <span>FC {result.fc_value?.toLocaleString() ?? '--'}</span>
                              <span>WAR {formatMetric(result.dynasty_roster_war)}</span>
                            </div>
                          </button>
                        ))
                    }
                  </div>
                )
                : (
                  <div className="my-values-search-empty">
                    Search at least two characters to add players who are missing from the default underdog-backed sheet.
                  </div>
                )
            }
          </div>

          <div className="my-values-editor-card">
            {
              detail.loading
                ? (
                  <LoadingState label="Loading player projections..." />
                )
                : null
            }

            {
              !detail.loading && selectedPlayer && marketValues && customValues && deltaValues
                ? (
                  <>
                    <div className="my-values-player-hero">
                      <div className="my-values-player-identity">
                        <PlayerAvatar
                          playerId={selectedPlayer.player_id}
                          name={selectedPlayer.name}
                          size="lg"
                        />
                        <div>
                          <div className="my-values-player-tag-row">
                            <span
                              className="my-values-player-position"
                              style={{
                                color: getPositionColor(
                                  selectedPlayer.position,
                                ),
                              }}
                            >
                              {selectedPlayer.position}
                            </span>
                            <span>{selectedPlayer.team ?? '--'}</span>
                            <span>Age {selectedPlayer.age ?? '--'}</span>
                            <span>{selectedPlayer.underdog_position_rank ?? 'No UD rank'}</span>
                            <span>KTC {formatMarketNumber(selectedPlayer.ktc_value)}</span>
                            <span>FC {formatMarketNumber(selectedPlayer.fc_value)}</span>
                          </div>
                          <h2>{selectedPlayer.name}</h2>
                          <p>
                            {selectedPlayerInPool
                              ? 'Editing a player already in your active projection pool.'
                              : 'This player will join your saved projection pool once you save a custom projection.'}
                          </p>
                        </div>
                      </div>

                      <div className="my-values-player-actions">
                        <button
                          type="button"
                          className="button-secondary"
                          onClick={handleReset}
                          disabled={saveProjection.saving}
                        >
                          Reset view
                        </button>
                        <button
                          type="button"
                          className="button-secondary"
                          onClick={() => {
                            void handleSave();
                          }}
                          disabled={saveProjection.saving}
                        >
                          {saveProjection.saving ? 'Saving...' : 'Save projections'}
                        </button>
                      </div>
                    </div>

                    <div className="my-values-metric-grid">
                      <MetricRail
                        label="Dynasty starter WAR"
                        market={marketValues.dynasty_starter_war}
                        mine={customValues.dynasty_starter_war}
                        delta={deltaValues.dynasty_starter_war}
                      />
                      <MetricRail
                        label="Dynasty roster WAR"
                        market={marketValues.dynasty_roster_war}
                        mine={customValues.dynasty_roster_war}
                        delta={deltaValues.dynasty_roster_war}
                      />
                      <MetricRail
                        label="Redraft starter WAR"
                        market={marketValues.redraft_starter_war}
                        mine={customValues.redraft_starter_war}
                        delta={deltaValues.redraft_starter_war}
                      />
                      <MetricRail
                        label="Redraft roster WAR"
                        market={marketValues.redraft_roster_war}
                        mine={customValues.redraft_roster_war}
                        delta={deltaValues.redraft_roster_war}
                      />
                    </div>

                    <div className="my-values-season-grid">
                      {
                        editableSeasons.map((season) => (
                          <article
                            key={season.season}
                            className="my-values-season-card"
                          >
                            <div className="my-values-season-card-header">
                              <div>
                                <p>{season.season}</p>
                                <h3>
                                  {
                                    season.season === currentProjectionSeason
                                      ? 'Current year'
                                      : 'Future year'
                                  }
                                </h3>
                              </div>
                              {
                                season.default_position_rank != null
                                  ? (
                                    <span className="my-values-default-pill">
                                      UD {selectedPlayer.position}{season.default_position_rank}
                                    </span>
                                  )
                                  : null
                              }
                            </div>

                              {
                              season.season === currentProjectionSeason
                                ? (
                                  <label className="my-values-outcome-field">
                                    <span>Projected finish</span>
                                    <input
                                      type="number"
                                      min={1}
                                      value={season.outcomes[0]?.position_rank ?? season.default_position_rank ?? 1}
                                      onChange={(event) => {
                                        handleCurrentRankChange(
                                          season.season,
                                          Number(event.target.value),
                                        );
                                      }}
                                    />
                                  </label>
                                )
                                : (
                                  <>
                                    <div className="my-values-season-actions">
                                      <p>
                                        Every future season starts with the default rank for the rest of the career. Add more weighted outcomes only where you want a different distribution.
                                      </p>
                                      <button
                                        type="button"
                                        className="button-secondary"
                                        onClick={() => {
                                          handleAddOutcome(
                                            season.season,
                                          );
                                        }}
                                      >
                                        Add outcome
                                      </button>
                                    </div>

                                    <div className="my-values-outcome-list">
                                      {
                                        season.outcomes.length === 0
                                          ? (
                                            <div className="my-values-empty-season">
                                              No future outcomes added yet.
                                            </div>
                                          )
                                          : season.outcomes.map((outcome, index) => (
                                            <div
                                              key={`${season.season}-${index}`}
                                              className="my-values-outcome-row"
                                            >
                                              <label className="my-values-outcome-field">
                                                <span>Rank</span>
                                                <input
                                                  type="number"
                                                  min={1}
                                                  value={outcome.position_rank}
                                                  onChange={(event) => {
                                                    handleOutcomeChange(
                                                      season.season,
                                                      index,
                                                      'position_rank',
                                                      Number(event.target.value),
                                                    );
                                                  }}
                                                />
                                              </label>

                                              <label className="my-values-outcome-field">
                                                <span>Probability %</span>
                                                <input
                                                  type="number"
                                                  min={1}
                                                  max={100}
                                                  value={outcome.probability}
                                                  onChange={(event) => {
                                                    handleOutcomeChange(
                                                      season.season,
                                                      index,
                                                      'probability',
                                                      Number(event.target.value),
                                                    );
                                                  }}
                                                />
                                              </label>

                                              <button
                                                type="button"
                                                className="button-secondary"
                                                onClick={() => {
                                                  handleRemoveOutcome(
                                                    season.season,
                                                    index,
                                                  );
                                                }}
                                              >
                                                Remove
                                              </button>
                                            </div>
                                          ))
                                      }
                                    </div>
                                  </>
                                )
                            }
                          </article>
                        ))
                      }
                    </div>
                  </>
                )
                : null
            }

            {
              !detail.loading && !selectedPlayer
                ? (
                  <div className="my-values-search-empty">
                    Select a player from the pool or search to start building personal values.
                  </div>
                )
                : null
            }
          </div>
        </section>
      </section>
    </div>
  );
};
