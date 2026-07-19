import './AdpPage.css';

import { useDeferredValue, useEffect, useMemo, useState } from 'react';
import { Database, Filter } from 'lucide-react';
import { useSearchParams } from 'react-router';

import { LoadingState } from '@/components/feedback/LoadingState';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { useAdp } from '@/hooks/useAdp';
import { useAdpMetadata } from '@/hooks/useAdpMetadata';
import { useAdpReport } from '@/hooks/useAdpReport';
import { notify } from '@/utils/notify';
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

type ViewMode =
  | 'board'
  | 'table';

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

const QUALIFICATION_LABELS: Record<string, string> = {
  qualified: 'Qualified',
  missing_picks: 'Missing picks',
  incomplete: 'Incomplete',
  mock: 'Mock',
  auction: 'Auction',
  keeper_draft: 'Keeper draft',
  unsupported_team_count: 'Unsupported team count',
  unsupported_round_count: 'Unsupported round count',
  missing_player_ids: 'Missing player IDs',
  unknown_format: 'Unknown format',
};

const DISCOVERY_SOURCE_LABELS: Record<string, string> = {
  existing_db: 'Existing DB seeds',
  user_id: 'User expansion',
  league_id: 'League expansion',
  draft_id: 'Direct draft seed',
};

const DISCOVERY_STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  processing: 'Processing',
  processed: 'Processed',
  failed: 'Failed',
  ignored: 'Ignored',
};

const DEFAULT_ADP_FILTERS: ADPFilters = {
  season: '2026',
  draft_kind: 'startup',
  qb_format: 'superflex',
  te_premium: '',
  scoring_format: '',
  team_count: 12,
  minimum_draft_count: 1,
  limit: 300,
  start_date: null,
  end_date: null,
};

const ADP_LIMIT_OPTIONS = [
  100,
  300,
  500,
  1000,
];

const BOARD_SORT_OPTIONS: Array<{
  value: SortColumn;
  label: string;
}> = [
  { value: 'overall_adp', label: 'ADP' },
  { value: 'median_pick', label: 'Median pick' },
  { value: 'name', label: 'Player name' },
  { value: 'position', label: 'Position' },
  { value: 'team', label: 'NFL team' },
  { value: 'draft_count', label: 'Draft count' },
  { value: 'selection_rate', label: 'Selection rate' },
];

const POSITION_THEME_CLASS: Record<string, string> = {
  QB: 'adp-player-card-qb',
  RB: 'adp-player-card-rb',
  WR: 'adp-player-card-wr',
  TE: 'adp-player-card-te',
  PICK: 'adp-player-card-pick',
};

function formatDateTime(
  value: string | null,
) {
  if (!value) {
    return '—';
  }

  return new Date(value).toLocaleString();
}


function formatDateInputValue(
  value: Date,
) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}


function formatPercent(
  value: number,
) {
  return `${(value * 100).toFixed(1)}%`;
}


function getSampleStrengthMessage(
  draftCount: number,
) {
  if (draftCount < 10) {
    return {
      tone: 'thin',
      title: 'Thin sample',
      body: 'This filter slice is built from fewer than 10 qualified drafts. Treat the rankings as directional only.',
    };
  }

  if (draftCount < 25) {
    return {
      tone: 'limited',
      title: 'Limited sample',
      body: 'This slice has some signal, but the draft count is still light enough that outliers can move player prices meaningfully.',
    };
  }

  return {
    tone: 'healthy',
    title: 'Healthy sample',
    body: 'This filter slice has enough qualified drafts that the board should be materially more stable.',
  };
}


function formatDataSource(
  value: string | null | undefined,
) {
  if (value === 'snapshot') {
    return 'Stored snapshot';
  }

  return 'Live aggregate';
}


function renderDistributionLabel(
  row: ADPDistributionItem,
  labelMap: Record<string, string> = {},
) {
  return labelMap[row.key] ?? row.key;
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


function readNumberParam(
  value: string | null,
  fallback: number,
) {
  if (!value) {
    return fallback;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed
    : fallback;
}


function readSortColumnParam(
  value: string | null,
): SortColumn {
  if (
    value === 'overall_adp'
    || value === 'median_pick'
    || value === 'min_pick'
    || value === 'max_pick'
    || value === 'standard_deviation'
    || value === 'name'
    || value === 'position'
    || value === 'team'
    || value === 'draft_count'
    || value === 'selection_rate'
  ) {
    return value;
  }

  return 'overall_adp';
}


function readSortDirectionParam(
  value: string | null,
): SortDirection {
  return value === 'desc'
    ? 'desc'
    : 'asc';
}


function readViewModeParam(
  value: string | null,
): ViewMode {
  return value === 'table'
    ? 'table'
    : 'board';
}


function readFiltersFromSearchParams(
  searchParams: URLSearchParams,
): ADPFilters {
  return {
    season: searchParams.get('season') ?? DEFAULT_ADP_FILTERS.season,
    draft_kind: searchParams.get('draft_kind') ?? DEFAULT_ADP_FILTERS.draft_kind,
    qb_format: searchParams.get('qb_format') ?? DEFAULT_ADP_FILTERS.qb_format,
    te_premium: searchParams.get('te_premium') ?? '',
    scoring_format: searchParams.get('scoring_format') ?? '',
    team_count: readNumberParam(
      searchParams.get('team_count'),
      DEFAULT_ADP_FILTERS.team_count ?? 12,
    ),
    minimum_draft_count: readNumberParam(
      searchParams.get('minimum_draft_count'),
      DEFAULT_ADP_FILTERS.minimum_draft_count ?? 1,
    ),
    limit: readNumberParam(
      searchParams.get('limit'),
      DEFAULT_ADP_FILTERS.limit ?? 300,
    ),
    start_date: searchParams.get('start_date'),
    end_date: searchParams.get('end_date'),
  };
}


function areFiltersEqual(
  left: ADPFilters,
  right: ADPFilters,
) {
  return (
    left.season === right.season
    && left.draft_kind === right.draft_kind
    && left.qb_format === right.qb_format
    && left.te_premium === right.te_premium
    && left.scoring_format === right.scoring_format
    && left.team_count === right.team_count
    && left.minimum_draft_count === right.minimum_draft_count
    && left.limit === right.limit
    && left.start_date === right.start_date
    && left.end_date === right.end_date
  );
}


function hasDistributionValue(
  rows: ADPDistributionItem[] | undefined,
  value: string | null | undefined,
) {
  if (!value) {
    return true;
  }

  return (rows ?? []).some((row) => row.key === value);
}


function buildBoardRounds(
  players: ADPPlayerRow[],
  boardSize: number,
) {
  const positionCounts = new Map<string, number>();
  const entries = players.map((player) => {
    const position = player.position ?? '—';
    const nextCount = (positionCounts.get(position) ?? 0) + 1;
    positionCounts.set(position, nextCount);

    return {
      player,
      positionRankLabel: `${position}${nextCount}`,
    };
  });

  const rounds = new Map<number, typeof entries>();

  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index];
    const round = Math.floor(index / boardSize) + 1;
    const current = rounds.get(round) ?? [];
    current.push(entry);
    rounds.set(round, current);
  }

  return Array.from(rounds.entries())
    .sort((left, right) => left[0] - right[0])
    .map(([round, roundPlayers]) => ({
      round,
      players: roundPlayers,
    }));
}


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
  ]);

  const sortedPlayers = useMemo(() => {
    const normalizedSearch = deferredPlayerSearch.trim().toLowerCase();
    const players = [...(query.data?.players ?? [])].filter((player) => {
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
    const positions = new Set<string>();
    for (const player of query.data?.players ?? []) {
      if (player.position) {
        positions.add(player.position);
      }
    }

    return Array.from(positions).sort();
  }, [query.data?.players]);

  const boardPlayers = useMemo(() => {
    const normalizedSearch = deferredPlayerSearch.trim().toLowerCase();
    const players = [...(query.data?.players ?? [])].filter((player) => {
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

          <section className={`adp-sample-health adp-sample-health-${sampleStrength.tone}`}>
            <span className="adp-section-kicker">Sample strength</span>
            <strong>{sampleStrength.title}</strong>
            <p>{sampleStrength.body}</p>
          </section>

          <section className="adp-active-filters">
            <span className="adp-section-kicker">Current slice</span>
            <div className="adp-active-filter-list">
              {activeFilterPills.map((pill) => (
                <span key={pill} className="adp-active-filter-pill">
                  {pill}
                </span>
              ))}
            </div>
          </section>

          <section className="adp-composition-card">
            <div className="adp-composition-header">
              <div>
                <span className="adp-section-kicker">Corpus health</span>
                <h2>Dataset quality and crawl shape</h2>
              </div>
              <small>
                These counts reflect the whole stored Sleeper corpus, not just the current board filter.
              </small>
            </div>

            <div className="adp-summary-grid">
              {corpusHealthCards.map((card) => (
                <article key={card.label} className="adp-summary-card">
                  <span>{card.label}</span>
                  <strong>{card.value}</strong>
                </article>
              ))}
            </div>

            <div className="adp-composition-grid">
              {reportDistributionGroups.map((group) => (
                <article key={group.label} className="adp-composition-group">
                  <span>{group.label}</span>
                  <div className="adp-composition-list">
                    {group.rows.length ? group.rows.slice(0, 8).map((row) => (
                      <div key={`${group.label}-${row.key}`} className="adp-composition-pill">
                        <strong>{group.render(row)}</strong>
                        <small>{row.count.toLocaleString()} drafts</small>
                      </div>
                    )) : (
                      <div className="adp-composition-empty">No tracked rows</div>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="adp-composition-card">
            <div className="adp-composition-header">
              <div>
                <span className="adp-section-kicker">Composition</span>
                <h2>Current sample makeup</h2>
              </div>
              <small>
                Counts reflect the discovered corpus available around this filter slice.
              </small>
            </div>

            <div className="adp-composition-grid">
              {sampleCompositionGroups.map((group) => (
                <article key={group.label} className="adp-composition-group">
                  <span>{group.label}</span>
                  <div className="adp-composition-list">
                    {group.rows.length ? group.rows.map((row) => (
                      <div key={`${group.label}-${row.key}`} className="adp-composition-pill">
                        <strong>{group.render(row)}</strong>
                        <small>{row.count.toLocaleString()} drafts</small>
                      </div>
                    )) : (
                      <div className="adp-composition-empty">No matching sample</div>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </section>

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

            <div className="adp-table-tools">
              <label>
                <span>Search players</span>
                <input
                  type="search"
                  value={playerSearch}
                  placeholder="Search by player, team, or position"
                  onChange={(event) => {
                    setPlayerSearch(event.target.value);
                  }}
                />
              </label>

              <label>
                <span>Position</span>
                <select
                  value={positionFilter}
                  onChange={(event) => {
                    setPositionFilter(event.target.value);
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
                    setViewMode(event.target.value as ViewMode);
                  }}
                >
                  <option value="board">Board style</option>
                  <option value="table">Table style</option>
                </select>
              </label>

              <label>
                <span>Board order</span>
                <select
                  value={sortColumn}
                  onChange={(event) => {
                    setSortColumn(event.target.value as SortColumn);
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
                    setSortDirection(event.target.value as SortDirection);
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
                  {(viewMode === 'board' ? boardPlayers.length : sortedPlayers.length).toLocaleString()}
                  {' / '}
                  {viewMode === 'board'
                    ? boardSize.toLocaleString()
                    : (query.data?.players.length ?? 0).toLocaleString()}
                </strong>
              </div>
            </div>

            {viewMode === 'board' ? (
              <>
                <div className="adp-board-note">
                  <span className="adp-section-kicker">Board style</span>
                  <p>
                    Draft-board layout always follows ADP order, grouped into
                    {' '}
                    {boardSize}
                    {' '}
                    picks per round. Scroll horizontally to read the full room.
                  </p>
                </div>

                <div className="adp-board">
                  <div className="adp-board-table-wrap">
                    <table className="adp-board-table">
                      <tbody>
                        {boardRounds.map((roundRow) => (
                          <tr key={`round-${roundRow.round}`} className="adp-board-table-row">
                            <th scope="row" className="adp-board-round-cell">
                              <span className="adp-board-round-label">
                                Round
                                {' '}
                                {roundRow.round}
                              </span>
                              <span className="adp-board-round-meta">
                                {(roundRow.round - 1) * boardSize + 1}
                                {' - '}
                                {((roundRow.round - 1) * boardSize) + roundRow.players.length}
                              </span>
                            </th>

                            {roundRow.players.map((entry, index) => {
                              const player = entry.player;
                              const slot = index + 1;
                              const overallPick = ((roundRow.round - 1) * boardSize) + slot;
                              const themeClass = POSITION_THEME_CLASS[player.position ?? ''] ?? '';

                              return (
                                <td
                                  key={`${roundRow.round}-${player.player_id}-${overallPick}`}
                                  className="adp-board-player-cell"
                                >
                                  <article className={`adp-player-card ${themeClass}`}>
                                    <div className="adp-player-card-topline">
                                      <span className="adp-player-slot">
                                        {roundRow.round}
                                        .
                                        {String(slot).padStart(2, '0')}
                                      </span>
                                      <span className="adp-player-rank">{entry.positionRankLabel}</span>
                                      <span className="adp-player-average">{player.overall_adp.toFixed(1)}</span>
                                    </div>

                                    <div className="adp-player-main">
                                      <div className="adp-player-copy">
                                        <strong className="adp-player-name">{player.name}</strong>
                                        <span className="adp-player-meta-compact">
                                          {player.position ?? '—'}
                                          {' '}
                                          ·
                                          {' '}
                                          {player.team ?? '—'}
                                        </span>
                                      </div>

                                      <PlayerAvatar
                                        playerId={player.player_id}
                                        name={player.name}
                                        size="md"
                                        className="adp-player-avatar"
                                      />
                                    </div>
                                  </article>
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : (
              <div className="adp-table-wrap">
                <table className="adp-table">
                  <thead>
                    <tr>
                      <th>ADP</th>
                      <th>Player</th>
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
