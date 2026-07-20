import './AdpPage.css';

import { useDeferredValue, useEffect, useMemo, useState } from 'react';
import { Database, Filter } from 'lucide-react';
import { useSearchParams } from 'react-router';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useAdp } from '@/hooks/useAdp';
import { useAdpMetadata } from '@/hooks/useAdpMetadata';
import { useAdpReport } from '@/hooks/useAdpReport';
import {
  CORE_FANTASY_POSITIONS,
  isCoreFantasyPosition,
} from '@/utils/positions';
import { notify } from '@/utils/notify';
import type {
  ADPDistributionItem,
  ADPFilters,
} from '@/types';
import {
  ADP_LIMIT_OPTIONS,
  DEFAULT_ADP_FILTERS,
  DISCOVERY_SOURCE_LABELS,
  DISCOVERY_STATUS_LABELS,
  DRAFT_KIND_LABELS,
  QB_FORMAT_LABELS,
  QUALIFICATION_LABELS,
  SCORING_LABELS,
  TEP_LABELS,
  areFiltersEqual,
  buildBoardDisplayRows,
  buildBoardRounds,
  buildDynamicOptions,
  compareRows,
  formatDataSource,
  formatDateInputValue,
  formatDateTime,
  formatPercent,
  getDefaultDraftOrderMode,
  getSampleStrengthMessage,
  hasDistributionValue,
  readDraftOrderModeParam,
  readFiltersFromSearchParams,
  readSortColumnParam,
  readSortDirectionParam,
  readViewModeParam,
  renderDistributionLabel,
  type DraftOrderMode,
  type SortColumn,
  type SortDirection,
  type ViewMode,
} from './adp.utils';
import { AdpBoard } from './AdpBoard';
import { AdpBoardToolbar } from './AdpBoardToolbar';
import { AdpSamplePanels } from './AdpSamplePanels';
import { AdpTable } from './AdpTable';

export const AdpPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<ADPFilters>(
    () => readFiltersFromSearchParams(searchParams),
  );
  const [playerSearch, setPlayerSearch] = useState(
    searchParams.get('player_search') ?? '',
  );
  const [positionFilter, setPositionFilter] = useState(
    searchParams.get('position') ?? '',
  );
  const [sortColumn, setSortColumn] = useState<SortColumn>(
    () => readSortColumnParam(searchParams.get('sort')),
  );
  const [sortDirection, setSortDirection] = useState<SortDirection>(
    () => readSortDirectionParam(searchParams.get('direction')),
  );
  const [viewMode, setViewMode] = useState<ViewMode>(
    () => readViewModeParam(searchParams.get('layout')),
  );
  const [draftOrderMode, setDraftOrderMode] = useState<DraftOrderMode>(
    () => readDraftOrderModeParam(
      searchParams.get('draft_order'),
      searchParams.get('draft_kind') ?? DEFAULT_ADP_FILTERS.draft_kind,
    ),
  );
  const deferredFilters = useDeferredValue(filters);
  const deferredPlayerSearch = useDeferredValue(playerSearch);
  const query = useAdp(deferredFilters);
  const metadataQuery = useAdpMetadata(deferredFilters);
  const reportQuery = useAdpReport();

  useEffect(() => {
    const nextFilters = readFiltersFromSearchParams(searchParams);
    const nextPlayerSearch = searchParams.get('player_search') ?? '';
    const nextPositionFilter = searchParams.get('position') ?? '';
    const nextSortColumn = readSortColumnParam(searchParams.get('sort'));
    const nextSortDirection = readSortDirectionParam(searchParams.get('direction'));
    const nextViewMode = readViewModeParam(searchParams.get('layout'));
    const nextDraftOrderMode = readDraftOrderModeParam(
      searchParams.get('draft_order'),
      nextFilters.draft_kind,
    );

    setFilters((current) => (
      areFiltersEqual(current, nextFilters)
        ? current
        : nextFilters
    ));
    setPlayerSearch((current) => (
      current === nextPlayerSearch
        ? current
        : nextPlayerSearch
    ));
    setPositionFilter((current) => (
      current === nextPositionFilter
        ? current
        : nextPositionFilter
    ));
    setSortColumn((current) => (
      current === nextSortColumn
        ? current
        : nextSortColumn
    ));
    setSortDirection((current) => (
      current === nextSortDirection
        ? current
        : nextSortDirection
    ));
    setViewMode((current) => (
      current === nextViewMode
        ? current
        : nextViewMode
    ));
    setDraftOrderMode((current) => (
      current === nextDraftOrderMode
        ? current
        : nextDraftOrderMode
    ));
  }, [searchParams]);

  useEffect(() => {
    const metadata = metadataQuery.data;
    if (!metadata) {
      return;
    }

    setFilters((current) => {
      const next: ADPFilters = { ...current };
      let changed = false;

      if (!hasDistributionValue(metadata.season_options, current.season)) {
        next.season = null;
        changed = true;
      }
      if (!hasDistributionValue(metadata.draft_kind_options, current.draft_kind)) {
        next.draft_kind = null;
        changed = true;
      }
      if (!hasDistributionValue(metadata.qb_format_options, current.qb_format)) {
        next.qb_format = null;
        changed = true;
      }
      if (!hasDistributionValue(metadata.te_premium_options, current.te_premium)) {
        next.te_premium = null;
        changed = true;
      }
      if (!hasDistributionValue(metadata.scoring_format_options, current.scoring_format)) {
        next.scoring_format = null;
        changed = true;
      }
      if (
        current.team_count != null
        && !hasDistributionValue(
          metadata.team_count_options,
          String(current.team_count),
        )
      ) {
        next.team_count = null;
        changed = true;
      }

      return changed
        ? next
        : current;
    });
  }, [metadataQuery.data]);

  useEffect(() => {
    const next = new URLSearchParams();

    if (filters.season) {
      next.set('season', filters.season);
    }
    if (filters.draft_kind) {
      next.set('draft_kind', filters.draft_kind);
    }
    if (filters.qb_format) {
      next.set('qb_format', filters.qb_format);
    }
    if (filters.te_premium) {
      next.set('te_premium', filters.te_premium);
    }
    if (filters.scoring_format) {
      next.set('scoring_format', filters.scoring_format);
    }
    if (filters.team_count != null) {
      next.set('team_count', String(filters.team_count));
    }
    if (filters.minimum_draft_count != null) {
      next.set('minimum_draft_count', String(filters.minimum_draft_count));
    }
    if (filters.limit != null) {
      next.set('limit', String(filters.limit));
    }
    if (filters.start_date) {
      next.set('start_date', filters.start_date);
    }
    if (filters.end_date) {
      next.set('end_date', filters.end_date);
    }
    if (playerSearch.trim()) {
      next.set('player_search', playerSearch.trim());
    }
    if (positionFilter) {
      next.set('position', positionFilter);
    }
    if (sortColumn !== 'overall_adp') {
      next.set('sort', sortColumn);
    }
    if (sortDirection !== 'asc') {
      next.set('direction', sortDirection);
    }
    if (viewMode !== 'board') {
      next.set('layout', viewMode);
    }
    if (draftOrderMode !== getDefaultDraftOrderMode(filters.draft_kind)) {
      next.set('draft_order', draftOrderMode);
    }

    if (next.toString() !== searchParams.toString()) {
      setSearchParams(next, { replace: true });
    }
  }, [
    filters,
    playerSearch,
    positionFilter,
    searchParams,
    setSearchParams,
    sortColumn,
    sortDirection,
    viewMode,
    draftOrderMode,
  ]);

  const sortedPlayers = useMemo(() => {
    const normalizedSearch = deferredPlayerSearch.trim().toLowerCase();
    const players = [...(query.data?.players ?? [])].filter((player) => {
      if (!isCoreFantasyPosition(player.position)) {
        return false;
      }

      if (
        positionFilter
        && (player.position ?? '') !== positionFilter
      ) {
        return false;
      }

      if (!normalizedSearch) {
        return true;
      }

      const haystack = [
        player.name,
        player.position ?? '',
        player.team ?? '',
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedSearch);
    });

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
    deferredPlayerSearch,
    positionFilter,
    query.data?.players,
    sortColumn,
    sortDirection,
  ]);

  const positionOptions = useMemo(() => {
    return CORE_FANTASY_POSITIONS.filter((position) => (
      (query.data?.players ?? []).some((player) => player.position === position)
    ));
  }, [query.data?.players]);

  const boardPlayers = useMemo(() => {
    const normalizedSearch = deferredPlayerSearch.trim().toLowerCase();
    const players = [...(query.data?.players ?? [])].filter((player) => {
      if (!isCoreFantasyPosition(player.position)) {
        return false;
      }

      if (
        positionFilter
        && (player.position ?? '') !== positionFilter
      ) {
        return false;
      }

      if (!normalizedSearch) {
        return true;
      }

      const haystack = [
        player.name,
        player.position ?? '',
        player.team ?? '',
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedSearch);
    });

    players.sort((left, right) => {
      if (left.overall_adp !== right.overall_adp) {
        return left.overall_adp - right.overall_adp;
      }

      return left.name.localeCompare(right.name);
    });

    return players;
  }, [
    deferredPlayerSearch,
    positionFilter,
    query.data?.players,
  ]);

  const boardSize = Math.max(filters.team_count ?? 12, 8);
  const boardRounds = useMemo(
    () => buildBoardRounds(boardPlayers, boardSize),
    [boardPlayers, boardSize],
  );
  const boardDisplayRows = useMemo(
    () => buildBoardDisplayRows(boardRounds, boardSize, draftOrderMode),
    [boardRounds, boardSize, draftOrderMode],
  );

  const applyDateWindow = (
    days: number | null,
  ) => {
    if (days == null) {
      setFilters((current) => ({
        ...current,
        start_date: null,
        end_date: null,
      }));
      return;
    }

    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);

    setFilters((current) => ({
      ...current,
      start_date: formatDateInputValue(startDate),
      end_date: formatDateInputValue(endDate),
    }));
  };

  const resetBoardView = () => {
    setFilters({
      ...DEFAULT_ADP_FILTERS,
    });
    setPlayerSearch('');
    setPositionFilter('');
    setSortColumn('overall_adp');
    setSortDirection('asc');
    setViewMode('board');
    setDraftOrderMode(getDefaultDraftOrderMode(DEFAULT_ADP_FILTERS.draft_kind));
  };

  const copyBoardLink = async () => {
    try {
      await navigator.clipboard.writeText(
        window.location.href,
      );
      notify.success('ADP board link copied.');
    } catch {
      notify.error('Could not copy the ADP board link.');
    }
  };

  const downloadCurrentBoardCsv = () => {
    const header = [
      'adp',
      'player',
      'position',
      'team',
      'median_pick',
      'min_pick',
      'max_pick',
      'standard_deviation',
      'draft_count',
      'selection_rate',
    ];
    const rows = sortedPlayers.map((player) => ([
      player.overall_adp.toFixed(2),
      player.name,
      player.position ?? '',
      player.team ?? '',
      player.median_pick.toFixed(1),
      String(player.min_pick),
      String(player.max_pick),
      player.standard_deviation?.toFixed(2) ?? '',
      String(player.draft_count),
      formatPercent(player.selection_rate),
    ]));
    const csv = [
      header,
      ...rows,
    ]
      .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'adp-board.csv';
    link.click();
    URL.revokeObjectURL(url);
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

  const sampleCompositionGroups = useMemo(() => ([
    {
      label: 'Seasons in corpus',
      rows: metadataQuery.data?.season_options ?? [],
      render: (row: ADPDistributionItem) => row.key,
    },
    {
      label: 'Draft kinds',
      rows: metadataQuery.data?.draft_kind_options ?? [],
      render: (row: ADPDistributionItem) => renderDistributionLabel(
        row,
        DRAFT_KIND_LABELS,
      ),
    },
    {
      label: 'QB formats',
      rows: metadataQuery.data?.qb_format_options ?? [],
      render: (row: ADPDistributionItem) => renderDistributionLabel(
        row,
        QB_FORMAT_LABELS,
      ),
    },
    {
      label: 'TE formats',
      rows: metadataQuery.data?.te_premium_options ?? [],
      render: (row: ADPDistributionItem) => renderDistributionLabel(
        row,
        TEP_LABELS,
      ),
    },
    {
      label: 'Scoring formats',
      rows: metadataQuery.data?.scoring_format_options ?? [],
      render: (row: ADPDistributionItem) => renderDistributionLabel(
        row,
        SCORING_LABELS,
      ),
    },
    {
      label: 'Team counts',
      rows: metadataQuery.data?.team_count_options ?? [],
      render: (row: ADPDistributionItem) => `${row.key} teams`,
    },
  ]), [
    metadataQuery.data?.draft_kind_options,
    metadataQuery.data?.qb_format_options,
    metadataQuery.data?.scoring_format_options,
    metadataQuery.data?.season_options,
    metadataQuery.data?.team_count_options,
    metadataQuery.data?.te_premium_options,
  ]);

  const sampleStrength = useMemo(
    () => getSampleStrengthMessage(
      query.data?.sample.draft_count ?? 0,
    ),
    [query.data?.sample.draft_count],
  );

  const activeFilterPills = useMemo(() => {
    const pills: string[] = [];

    if (filters.season) {
      pills.push(filters.season);
    }
    if (filters.draft_kind) {
      pills.push(DRAFT_KIND_LABELS[filters.draft_kind] ?? filters.draft_kind);
    }
    if (filters.qb_format) {
      pills.push(QB_FORMAT_LABELS[filters.qb_format] ?? filters.qb_format);
    }
    if (filters.te_premium) {
      pills.push(TEP_LABELS[filters.te_premium] ?? filters.te_premium);
    }
    if (filters.scoring_format) {
      pills.push(SCORING_LABELS[filters.scoring_format] ?? filters.scoring_format);
    }
    if (filters.team_count != null) {
      pills.push(`${filters.team_count} teams`);
    }
    if (filters.start_date || filters.end_date) {
      pills.push(
        `${filters.start_date ?? 'start'} to ${filters.end_date ?? 'today'}`,
      );
    }
    if (filters.limit != null) {
      pills.push(`Top ${filters.limit}`);
    }
    if (positionFilter) {
      pills.push(`Pos ${positionFilter}`);
    }
    if (playerSearch.trim()) {
      pills.push(`Search: ${playerSearch.trim()}`);
    }

    return pills;
  }, [
    filters.draft_kind,
    filters.end_date,
    filters.qb_format,
    filters.scoring_format,
    filters.season,
    filters.start_date,
    filters.team_count,
    filters.te_premium,
    filters.limit,
    playerSearch,
    positionFilter,
  ]);

  const corpusHealthCards = useMemo(() => {
    const report = reportQuery.data;
    if (!report) {
      return [];
    }

    return [
      {
        label: 'Corpus qualified drafts',
        value: report.qualified_draft_count.toLocaleString(),
      },
      {
        label: 'Corpus excluded drafts',
        value: report.excluded_draft_count.toLocaleString(),
      },
      {
        label: 'Unique leagues',
        value: report.unique_league_count.toLocaleString(),
      },
      {
        label: 'Discovery roots',
        value: report.unique_root_source_count.toLocaleString(),
      },
      {
        label: 'Corpus earliest draft',
        value: formatDateTime(report.earliest_draft_at),
      },
      {
        label: 'Corpus latest draft',
        value: formatDateTime(report.latest_draft_at),
      },
    ];
  }, [reportQuery.data]);

  const reportDistributionGroups = useMemo(() => {
    const report = reportQuery.data;
    if (!report) {
      return [];
    }

    return [
      {
        label: 'Exclusion reasons',
        rows: report.qualification_code_distribution.filter((row) => row.key !== 'qualified'),
        render: (row: ADPDistributionItem) => renderDistributionLabel(
          row,
          QUALIFICATION_LABELS,
        ),
      },
      {
        label: 'Discovery sources',
        rows: report.discovery_source_distribution,
        render: (row: ADPDistributionItem) => renderDistributionLabel(
          row,
          DISCOVERY_SOURCE_LABELS,
        ),
      },
      {
        label: 'Discovery depth',
        rows: report.discovery_depth_distribution,
        render: (row: ADPDistributionItem) => `Depth ${row.key}`,
      },
      {
        label: 'Node statuses',
        rows: report.discovery_status_distribution,
        render: (row: ADPDistributionItem) => renderDistributionLabel(
          row,
          DISCOVERY_STATUS_LABELS,
        ),
      },
    ];
  }, [reportQuery.data]);

  return (
    <div className="adp-page">
      <section className="page-header adp-hero">
        <div>
          <p className="page-eyebrow">Rankings</p>
          <h1 className="page-title">Sleeper ADP board</h1>
          <p className="page-description">
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
          <div className="adp-filters-actions">
            <div className="adp-filters-note">
              <Filter size={16} />
              <span>Changing filters requeries the cached `/adp` dataset.</span>
            </div>
            <button
              type="button"
              className="site-button site-button-secondary"
              onClick={copyBoardLink}
            >
              Copy link
            </button>
            <button
              type="button"
              className="site-button site-button-secondary"
              onClick={resetBoardView}
            >
              Reset board
            </button>
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
            <span>Row limit</span>
            <select
              value={String(filters.limit ?? DEFAULT_ADP_FILTERS.limit ?? 300)}
              onChange={(event) => {
                setFilters((current) => ({
                  ...current,
                  limit: Number(event.target.value),
                }));
              }}
            >
              {ADP_LIMIT_OPTIONS.map((limit) => (
                <option key={limit} value={limit}>
                  Top {limit}
                </option>
              ))}
            </select>
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

          <div className="adp-filter-window">
            <span>Date presets</span>
            <div className="adp-filter-window-buttons">
              <button
                type="button"
                className="site-button site-button-secondary"
                onClick={() => {
                  applyDateWindow(30);
                }}
              >
                Last 30d
              </button>
              <button
                type="button"
                className="site-button site-button-secondary"
                onClick={() => {
                  applyDateWindow(60);
                }}
              >
                Last 60d
              </button>
              <button
                type="button"
                className="site-button site-button-secondary"
                onClick={() => {
                  applyDateWindow(90);
                }}
              >
                Last 90d
              </button>
              <button
                type="button"
                className="site-button site-button-secondary"
                onClick={() => {
                  applyDateWindow(null);
                }}
              >
                All time
              </button>
            </div>
          </div>

        </div>
      </section>

      {query.isLoading && !query.data ? (
        <LoadingState label="Loading ADP board" />
      ) : (
        <>
          <AdpSamplePanels
            sample={query.data?.sample}
            sampleStrength={sampleStrength}
            activeFilterPills={activeFilterPills}
            corpusHealthCards={corpusHealthCards}
            reportDistributionGroups={reportDistributionGroups}
            sampleCompositionGroups={sampleCompositionGroups}
          />

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
                  onClick={downloadCurrentBoardCsv}
                >
                  Export CSV
                </button>
                <small>
                  {formatDataSource(query.data?.sample.data_source)}
                </small>
                <small>
                  Generated {formatDateTime(query.data?.sample.generated_at ?? null)}
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
              visibleCount={viewMode === 'board' ? boardPlayers.length : sortedPlayers.length}
              secondaryCount={viewMode === 'board' ? boardSize : (query.data?.players.length ?? 0)}
              onPlayerSearchChange={setPlayerSearch}
              onPositionFilterChange={setPositionFilter}
              onViewModeChange={setViewMode}
              onDraftOrderModeChange={setDraftOrderMode}
              onSortColumnChange={setSortColumn}
              onSortDirectionChange={setSortDirection}
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

            {!(viewMode === 'board' ? boardPlayers.length : sortedPlayers.length) ? (
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
