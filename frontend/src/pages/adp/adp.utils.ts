import type {
  ADPDistributionItem,
  ADPFilters,
  ADPPlayerRow,
} from '@/types';

export type SortColumn =
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

export type SortDirection =
  | 'asc'
  | 'desc';

export type ViewMode =
  | 'board'
  | 'table';

export type DraftOrderMode =
  | 'snake'
  | 'linear'
  | 'third_round_reversal';

export const DRAFT_KIND_LABELS: Record<string, string> = {
  startup: 'Startup',
  rookie: 'Rookie',
  supplemental: 'Supplemental',
};

export const QB_FORMAT_LABELS: Record<string, string> = {
  one_qb: '1QB',
  superflex: 'Superflex',
  two_qb: '2QB',
};

export const TEP_LABELS: Record<string, string> = {
  none: 'Non-TEP',
  premium: 'TE premium',
};

export const SCORING_LABELS: Record<string, string> = {
  standard: 'Standard',
  half_ppr: 'Half PPR',
  ppr: 'PPR',
  custom: 'Custom',
};

export const QUALIFICATION_LABELS: Record<string, string> = {
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

export const DISCOVERY_SOURCE_LABELS: Record<string, string> = {
  existing_db: 'Existing DB seeds',
  user_id: 'User expansion',
  league_id: 'League expansion',
  draft_id: 'Direct draft seed',
};

export const DISCOVERY_STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  processing: 'Processing',
  processed: 'Processed',
  failed: 'Failed',
  ignored: 'Ignored',
};

export const DEFAULT_ADP_FILTERS: ADPFilters = {
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

export const ADP_LIMIT_OPTIONS = [
  100,
  300,
  500,
  1000,
];

export const BOARD_SORT_OPTIONS: Array<{
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

export const POSITION_THEME_CLASS: Record<string, string> = {
  QB: 'adp-player-card-qb',
  RB: 'adp-player-card-rb',
  WR: 'adp-player-card-wr',
  TE: 'adp-player-card-te',
  PICK: 'adp-player-card-pick',
};

export const DRAFT_ORDER_LABELS: Record<DraftOrderMode, string> = {
  snake: 'Snake',
  linear: 'Linear',
  third_round_reversal: '3RR',
};

export function formatDateTime(
  value: string | null,
) {
  if (!value) {
    return '-';
  }

  return new Date(value).toLocaleString();
}

export function formatDateInputValue(
  value: Date,
) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatPercent(
  value: number,
) {
  return `${(value * 100).toFixed(1)}%`;
}

export function getSampleStrengthMessage(
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

export function formatDataSource(
  value: string | null | undefined,
) {
  if (value === 'snapshot') {
    return 'Stored snapshot';
  }

  return 'Live aggregate';
}

export function renderDistributionLabel(
  row: ADPDistributionItem,
  labelMap: Record<string, string> = {},
) {
  return labelMap[row.key] ?? row.key;
}

export function buildDynamicOptions(
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

export function compareRows(
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

export function readSortColumnParam(
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

export function readSortDirectionParam(
  value: string | null,
): SortDirection {
  return value === 'desc'
    ? 'desc'
    : 'asc';
}

export function readViewModeParam(
  value: string | null,
): ViewMode {
  return value === 'table'
    ? 'table'
    : 'board';
}

export function getDefaultDraftOrderMode(
  draftKind: string | null | undefined,
): DraftOrderMode {
  return draftKind === 'rookie'
    ? 'linear'
    : 'snake';
}

export function readDraftOrderModeParam(
  value: string | null,
  draftKind: string | null | undefined,
): DraftOrderMode {
  if (
    value === 'snake'
    || value === 'linear'
    || value === 'third_round_reversal'
  ) {
    return value;
  }

  return getDefaultDraftOrderMode(draftKind);
}

export function readFiltersFromSearchParams(
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

export function areFiltersEqual(
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

export function hasDistributionValue(
  rows: ADPDistributionItem[] | undefined,
  value: string | null | undefined,
) {
  if (!value) {
    return true;
  }

  return (rows ?? []).some((row) => row.key === value);
}

export function buildBoardRounds(
  players: ADPPlayerRow[],
  boardSize: number,
) {
  const positionCounts = new Map<string, number>();
  const entries = players.map((player) => {
    const position = player.position ?? '-';
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

export function getDisplaySlotForColumn(
  round: number,
  columnIndex: number,
  boardSize: number,
  draftOrderMode: DraftOrderMode,
) {
  const ascending = columnIndex + 1;
  const descending = boardSize - columnIndex;

  if (draftOrderMode === 'linear') {
    return ascending;
  }

  if (draftOrderMode === 'snake') {
    return round % 2 === 1
      ? ascending
      : descending;
  }

  if (round === 1) {
    return ascending;
  }

  if (round === 2 || round === 3) {
    return descending;
  }

  return round % 2 === 0
    ? ascending
    : descending;
}

export function buildBoardDisplayRows(
  rounds: ReturnType<typeof buildBoardRounds>,
  boardSize: number,
  draftOrderMode: DraftOrderMode,
) {
  return rounds.map((roundRow) => {
    const cells = Array.from({ length: boardSize }, (_, columnIndex) => {
      const displaySlot = getDisplaySlotForColumn(
        roundRow.round,
        columnIndex,
        boardSize,
        draftOrderMode,
      );
      const playerIndex = displaySlot - 1;
      const entry = roundRow.players[playerIndex] ?? null;
      const overallPick = ((roundRow.round - 1) * boardSize) + displaySlot;

      return {
        columnIndex,
        displaySlot,
        overallPick,
        entry,
      };
    });

    return {
      round: roundRow.round,
      cells,
    };
  });
}
