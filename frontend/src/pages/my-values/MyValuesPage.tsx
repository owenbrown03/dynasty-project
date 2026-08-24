import './MyValuesPage.css';

import { AxiosError } from 'axios';
import {
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { Skeleton } from '@/components/feedback/Skeleton';
import { useValuePreference } from '@/context/useValuePreference';
import { useLeagueOverview } from '@/hooks/sleeper/useLeagues';
import {
  usePersonalValueDetail,
  usePersonalValuePool,
  usePersonalValueSearch,
  useResetPersonalValueRankings,
  useSavePersonalValueDetail,
  useSyncUnderdogDefaults,
} from '@/hooks/sleeper/usePersonalValues';
import type {
  PersonalProjectionOutcomeItem,
  PersonalProjectionSeasonItem,
} from '@/types';
import { notify } from '@/utils/notify';
import {
  SORT_LABELS,
  buildNextTableFilter,
  buildEmptyOutcome,
  cloneSeasons,
  comparePoolItems,
  getDefaultFutureOutcomes,
  getDefaultSortColumn,
  getPoolPlayerIds,
  itemMatchesFilter,
  type FutureProjectionMode,
  type SortColumn,
  type SortDirection,
  type TableFilter,
} from './myValues.utils';
import { MyValuesMetricCard } from './MyValuesMetricCard';
import { MyValuesPlayerHero } from './MyValuesPlayerHero';
import { MyValuesPoolPanel } from './MyValuesPoolPanel';
import { MyValuesRankingsBoard } from './MyValuesRankingsBoard';
import { MyValuesSearchCard } from './MyValuesSearchCard';

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

function MyValuesEditorSkeleton() {
  return (
    <div className="my-values-editor-skeleton" role="status" aria-live="polite">
      <span className="skeleton-sr-label">Loading player projections...</span>

      <div className="my-values-player-hero">
        <div className="my-values-player-identity">
          <Skeleton width={52} height={52} radius={6} />
          <div>
            <div className="my-values-player-tag-row">
              {
                Array.from({ length: 6 }).map((_, index) => (
                  <Skeleton width={index === 0 ? 34 : 58} variant="text" key={index} />
                ))
              }
            </div>
            <Skeleton width={210} height={32} />
            <Skeleton width={320} variant="text" />
          </div>
        </div>

        <div className="my-values-player-actions">
          <Skeleton width={104} height={42} />
          <Skeleton width={138} height={42} />
        </div>
      </div>

      <div className="my-values-metric-grid">
        {
          Array.from({ length: 4 }).map((_, index) => (
            <div className="my-values-metric-card" key={index}>
              <Skeleton width={140} variant="text" />
              <Skeleton width={76} height={36} />
              <div className="my-values-metric-meta">
                <Skeleton width={92} variant="text" />
                <Skeleton width={74} variant="text" />
              </div>
            </div>
          ))
        }
      </div>

      <div className="my-values-season-grid">
        {
          Array.from({ length: 2 }).map((_, index) => (
            <article className="my-values-season-card" key={index}>
              <div className="my-values-season-card-header">
                <div>
                  <Skeleton width={54} variant="text" />
                  <Skeleton width={130} variant="title" />
                </div>
                <Skeleton width={64} height={28} />
              </div>
              <Skeleton height={46} />
              <Skeleton width="82%" variant="text" />
            </article>
          ))
        }
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
  const resetRankings = useResetPersonalValueRankings();
  const syncUnderdog = useSyncUnderdogDefaults();
  const [editableSeasons, setEditableSeasons] = useState<
    PersonalProjectionSeasonItem[]
  >([]);
  const [viewMode, setViewMode] = useState<
    'editor' | 'rankings'
  >('editor');
  const [futureProjectionMode, setFutureProjectionMode] =
    useState<FutureProjectionMode>('default');
  const [specificFutureYear, setSpecificFutureYear] = useState<
    number | ''
  >('');
  const [defaultFutureOutcomes, setDefaultFutureOutcomes] = useState<
    PersonalProjectionOutcomeItem[]
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
    const detailData = detail.data;

    if (detailData) {
      const cloned = cloneSeasons(detailData.seasons);
      setEditableSeasons(cloned);

      const firstFutureSeason = cloned.find(
        (season) => season.season !== detailData.context.season,
      );

      setDefaultFutureOutcomes(
        getDefaultFutureOutcomes(
          cloned,
          detailData.context.season,
        ),
      );
      setSpecificFutureYear(
        firstFutureSeason?.season ?? '',
      );
      setFutureProjectionMode('default');
    } else {
      setEditableSeasons([]);
      setDefaultFutureOutcomes([]);
      setSpecificFutureYear('');
      setFutureProjectionMode('default');
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
          : searchSort === 'adp'
            ? left.adp_value
          : searchSort === 'my_war'
            || searchSort === 'market_war'
            ? left.dynasty_roster_war
            : left.ktc_value
      ) ?? Number.NEGATIVE_INFINITY;
      const rightMetric = (
        searchSort === 'fantasycalc'
          ? right.fc_value
          : searchSort === 'adp'
            ? right.adp_value
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
          is_customized: (
            seasonItem.season !== currentProjectionSeason
              ? true
              : seasonItem.is_customized
          ),
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
          is_customized: (
            seasonItem.season !== currentProjectionSeason
              ? true
              : seasonItem.is_customized
          ),
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
          is_customized: (
            seasonItem.season !== currentProjectionSeason
              ? true
              : seasonItem.is_customized
          ),
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

        if (seasonItem.outcomes.length <= 1) {
          return seasonItem;
        }

        return {
          ...seasonItem,
          is_customized: (
            seasonItem.season !== currentProjectionSeason
              ? true
              : seasonItem.is_customized
          ),
          outcomes: seasonItem.outcomes.filter(
            (_, index) => index !== outcomeIndex,
          ),
        };
      }),
    );
  };

  const handleDefaultFutureOutcomeChange = (
    outcomeIndex: number,
    field: 'position_rank' | 'probability',
    value: number,
  ) => {
    setDefaultFutureOutcomes((current) =>
      current.map((outcome, index) =>
        index === outcomeIndex
          ? {
            ...outcome,
            [field]: value,
          }
          : outcome,
      ),
    );
  };

  const handleAddDefaultFutureOutcome = () => {
    setDefaultFutureOutcomes((current) => [
      ...current,
      buildEmptyOutcome(),
    ]);
  };

  const handleRemoveDefaultFutureOutcome = (
    outcomeIndex: number,
  ) => {
    setDefaultFutureOutcomes((current) =>
      current.length <= 1
        ? current
        : current.filter(
          (_, index) => index !== outcomeIndex,
        ),
    );
  };

  const handleSyncUnderdogAll = async () => {
    if (!leagueId) return;

    if (
      !window.confirm(
        'Freeze current Underdog ranks as your personal values for every player still on defaults? Customized players are untouched.',
      )
    ) {
      return;
    }

    try {
      const result = await syncUnderdog.syncDefaults({
        league_id: leagueId,
      });
      notify.success(
        `Synced ${result.reset_players} defaulted players to Underdog ranks.`,
      );
    } catch {
      notify.error('Could not sync Underdog defaults.');
    }
  };

  const handleResetAllToUnderdog = async () => {
    if (!leagueId) return;

    if (
      !window.confirm(
        'Remove ALL your personal customizations (every position, every season) and reset to Underdog defaults?',
      )
    ) {
      return;
    }

    try {
      const result = await resetRankings.resetRankings({
        league_id: leagueId,
      });
      notify.success(
        `Reset ${result.reset_players} players to Underdog defaults.`,
      );
    } catch {
      notify.error('Could not reset to Underdog defaults.');
    }
  };

  const handleReset = () => {
    const detailData = detail.data;

    if (!detailData) {
      return;
    }

    setEditableSeasons(
      cloneSeasons(detailData.seasons),
    );
    setDefaultFutureOutcomes(
      getDefaultFutureOutcomes(
        detailData.seasons,
        detailData.context.season,
      ),
    );
  };

  const handleSave = async () => {
    if (!leagueId || !selectedPlayerId) {
      return;
    }

    try {
      const currentSeason = currentProjectionSeason;
      const fallbackFuturePayload = getDefaultFutureOutcomes(
        editableSeasons,
        currentSeason ?? 0,
      );
      const defaultFuturePayload = (
        defaultFutureOutcomes.length
          ? defaultFutureOutcomes
          : fallbackFuturePayload
      ).map(
        (outcome) => ({
          position_rank: Number(outcome.position_rank),
          probability: Number(outcome.probability),
        }),
      );
      const submittedSeasons = editableSeasons.map(
        (season) => {
          if (
            currentSeason != null
            && season.season !== currentSeason
            && (
              futureProjectionMode === 'default'
              || season.outcomes.length === 0
            )
          ) {
            return {
              ...season,
              outcomes: defaultFuturePayload,
            };
          }

          return season;
        },
      );

      await saveProjection.savePersonalValue({
        leagueId,
        playerId: selectedPlayerId,
        payload: {
          seasons: submittedSeasons.map(
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
      buildNextTableFilter(current),
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
  const currentEditableSeason = editableSeasons.find(
    (season) => season.season === currentProjectionSeason,
  );
  const futureSeasons = editableSeasons.filter(
    (season) => season.season !== currentProjectionSeason,
  );
  const minFutureSeason = futureSeasons[0]?.season ?? '';
  const maxFutureSeason = (
    futureSeasons[futureSeasons.length - 1]?.season
    ?? ''
  );
  const selectedFutureSeason = futureSeasons.find(
    (season) => season.season === specificFutureYear,
  ) ?? futureSeasons[0];
  const visibleFutureOutcomes = (
    futureProjectionMode === 'default'
      ? defaultFutureOutcomes
      : selectedFutureSeason?.outcomes ?? []
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
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Projections</p>
          <h1 className="page-title">
            Personal values
          </h1>
          <p className="page-description">
            Start from Underdog rank defaults, layer in your own weighted finish outcomes, and compare market WAR against your custom dynasty view inside a real league context.
          </p>
        </div>

        <div className="my-values-header-controls">
          <button
            type="button"
            className="button-secondary"
            disabled={syncUnderdog.saving}
            onClick={() => {
              void handleSyncUnderdogAll();
            }}
          >
            {syncUnderdog.saving
              ? 'Syncing…'
              : 'Sync defaults from Underdog'}
          </button>
          <button
            type="button"
            className="button-secondary"
            disabled={resetRankings.saving}
            onClick={() => {
              void handleResetAllToUnderdog();
            }}
          >
            {resetRankings.saving
              ? 'Resetting…'
              : 'Reset all to Underdog'}
          </button>
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
        </div>
      </section>

      <div className="page-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === 'editor'}
          className={`league-dashboard-tab${viewMode === 'editor' ? ' active' : ''}`}
          onClick={() => setViewMode('editor')}
        >
          Editor
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === 'rankings'}
          className={`league-dashboard-tab${viewMode === 'rankings' ? ' active' : ''}`}
          onClick={() => setViewMode('rankings')}
        >
          Rankings board
        </button>
      </div>

      {viewMode === 'rankings' && (
        <MyValuesRankingsBoard
          leagueId={leagueId || undefined}
          onEditPlayer={(playerId) => {
            setSelectedPlayerId(playerId);
            setViewMode('editor');
          }}
        />
      )}

      <section
        className="my-values-workspace"
        style={
          viewMode === 'rankings'
            ? { display: 'none' }
            : undefined
        }
      >
        <MyValuesPoolPanel
          leagueName={selectedLeagueName}
          fetching={pool.fetching}
          loading={pool.loading}
          searchSort={searchSort}
          sortDirection={sortDirection}
          tableFilters={tableFilters}
          filteredPoolItems={filteredPoolItems}
          filteredPoolCount={filteredPoolCount}
          pageSummaryMetric={pageSummaryMetric}
          selectedPlayerId={selectedPlayerId}
          onSearchSortChange={setSearchSort}
          onSortDirectionChange={setSortDirection}
          onAddTableFilter={addTableFilter}
          onUpdateTableFilter={updateTableFilter}
          onRemoveTableFilter={removeTableFilter}
          onHeaderSort={handleHeaderSort}
          onSelectPlayer={setSelectedPlayerId}
        />

        <section className="my-values-editor-panel">
          <MyValuesSearchCard
            searchTerm={searchTerm}
            searchEnabled={search.enabled}
            loading={search.loading}
            fetching={search.fetching}
            results={sortedSearchResults}
            onSearchTermChange={setSearchTerm}
            onSelectPlayer={setSelectedPlayerId}
          />

          <div className="my-values-editor-card">
            {
              detail.loading
                ? (
                  <MyValuesEditorSkeleton />
                )
                : null
            }

            {
              !detail.loading && selectedPlayer && marketValues && customValues && deltaValues
                ? (
                  <>
                    <MyValuesPlayerHero
                      player={selectedPlayer}
                      playerInPool={selectedPlayerInPool}
                      saving={saveProjection.saving}
                      onReset={handleReset}
                      onSave={() => {
                        void handleSave();
                      }}
                    />

                    <div className="my-values-metric-grid">
                      <MyValuesMetricCard
                        label="Dynasty starter WAR"
                        market={marketValues.dynasty_starter_war}
                        mine={customValues.dynasty_starter_war}
                        delta={deltaValues.dynasty_starter_war}
                      />
                      <MyValuesMetricCard
                        label="Dynasty roster WAR"
                        market={marketValues.dynasty_roster_war}
                        mine={customValues.dynasty_roster_war}
                        delta={deltaValues.dynasty_roster_war}
                      />
                      <MyValuesMetricCard
                        label="Redraft starter WAR"
                        market={marketValues.redraft_starter_war}
                        mine={customValues.redraft_starter_war}
                        delta={deltaValues.redraft_starter_war}
                      />
                      <MyValuesMetricCard
                        label="Redraft roster WAR"
                        market={marketValues.redraft_roster_war}
                        mine={customValues.redraft_roster_war}
                        delta={deltaValues.redraft_roster_war}
                      />
                    </div>

                    <div className="my-values-season-grid">
                      {
                        currentEditableSeason
                          ? (
                            <article
                              className="my-values-season-card"
                            >
                              <div className="my-values-season-card-header">
                                <div>
                                  <p>{currentEditableSeason.season}</p>
                                  <h3>Current year</h3>
                                </div>
                                {
                                  currentEditableSeason.default_position_rank != null
                                    ? (
                                      <span className="my-values-default-pill">
                                        UD {selectedPlayer.position}{currentEditableSeason.default_position_rank}
                                      </span>
                                    )
                                    : null
                                }
                              </div>

                              <label className="my-values-outcome-field my-values-current-rank-field">
                                <span>Projected finish</span>
                                <input
                                  type="number"
                                  min={1}
                                  value={currentEditableSeason.outcomes[0]?.position_rank ?? currentEditableSeason.default_position_rank ?? 1}
                                  onChange={(event) => {
                                    handleCurrentRankChange(
                                      currentEditableSeason.season,
                                      Number(event.target.value),
                                    );
                                  }}
                                />
                              </label>
                            </article>
                          )
                          : null
                      }

                      {
                        selectedFutureSeason
                          ? (
                          <article
                            className="my-values-season-card"
                          >
                            <div className="my-values-season-card-header">
                              <div>
                                <p>
                                  {
                                    futureProjectionMode === 'default'
                                      ? `${minFutureSeason}-${maxFutureSeason}`
                                      : selectedFutureSeason.season
                                  }
                                </p>
                                <h3>Future years</h3>
                              </div>
                              {
                                selectedFutureSeason.default_position_rank != null
                                  ? (
                                    <span className="my-values-default-pill">
                                      UD {selectedPlayer.position}{selectedFutureSeason.default_position_rank}
                                    </span>
                                  )
                                  : null
                              }
                            </div>

                            <div className="my-values-future-controls">
                              <label className="my-values-outcome-field">
                                <span>Future window</span>
                                <select
                                  value={futureProjectionMode}
                                  onChange={(event) => {
                                    setFutureProjectionMode(
                                      event.target.value as FutureProjectionMode,
                                    );
                                  }}
                                >
                                  <option value="default">Default future years</option>
                                  <option value="year">Specific year</option>
                                </select>
                              </label>

                              {
                                futureProjectionMode === 'year'
                                  ? (
                                    <label className="my-values-outcome-field">
                                      <span>Year</span>
                                      <input
                                        type="number"
                                        min={minFutureSeason || undefined}
                                        max={maxFutureSeason || undefined}
                                        value={specificFutureYear}
                                        onChange={(event) => {
                                          const nextYear = Number(event.target.value);
                                          setSpecificFutureYear(
                                            Number.isNaN(nextYear)
                                              ? ''
                                              : nextYear,
                                          );
                                        }}
                                        onBlur={() => {
                                          if (
                                            specificFutureYear === ''
                                            || !futureSeasons.some(
                                              (season) => season.season === specificFutureYear,
                                            )
                                          ) {
                                            setSpecificFutureYear(
                                              selectedFutureSeason.season,
                                            );
                                          }
                                        }}
                                      />
                                    </label>
                                  )
                                  : null
                              }
                            </div>

                            <div className="my-values-season-actions">
                              <p>
                                {
                                  futureProjectionMode === 'default'
                                    ? 'These outcomes apply to future years that have not been customized individually.'
                                    : `Editing ${selectedFutureSeason.season} only.`
                                }
                              </p>
                              <button
                                type="button"
                                className="button-secondary"
                                onClick={() => {
                                  if (futureProjectionMode === 'default') {
                                    handleAddDefaultFutureOutcome();
                                    return;
                                  }

                                  handleAddOutcome(
                                    selectedFutureSeason.season,
                                  );
                                }}
                              >
                                Add outcome
                              </button>
                            </div>

                            <div className="my-values-outcome-list">
                              {
                                visibleFutureOutcomes.length === 0
                                  ? (
                                    <div className="my-values-empty-season">
                                      Future outcomes default to the player&apos;s Underdog rank.
                                    </div>
                                  )
                                  : visibleFutureOutcomes.map((outcome, index) => (
                                    <div
                                      key={`${futureProjectionMode}-${selectedFutureSeason.season}-${index}`}
                                      className="my-values-outcome-row"
                                    >
                                      <label className="my-values-outcome-field">
                                        <span>Rank</span>
                                        <input
                                          type="number"
                                          min={1}
                                          value={outcome.position_rank}
                                          onChange={(event) => {
                                            if (futureProjectionMode === 'default') {
                                              handleDefaultFutureOutcomeChange(
                                                index,
                                                'position_rank',
                                                Number(event.target.value),
                                              );
                                              return;
                                            }

                                            handleOutcomeChange(
                                              selectedFutureSeason.season,
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
                                            if (futureProjectionMode === 'default') {
                                              handleDefaultFutureOutcomeChange(
                                                index,
                                                'probability',
                                                Number(event.target.value),
                                              );
                                              return;
                                            }

                                            handleOutcomeChange(
                                              selectedFutureSeason.season,
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
                                        disabled={visibleFutureOutcomes.length <= 1}
                                        onClick={() => {
                                          if (futureProjectionMode === 'default') {
                                            handleRemoveDefaultFutureOutcome(index);
                                            return;
                                          }

                                          handleRemoveOutcome(
                                            selectedFutureSeason.season,
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
                          </article>
                          )
                          : null
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
