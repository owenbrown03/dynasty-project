import type {
  PersonalProjectionOutcomeItem,
  PersonalProjectionSeasonItem,
  PersonalValuePoolItem,
  ValueBasis,
} from '@/types';
import { CORE_FANTASY_POSITION_ORDER } from '@/utils/positions';

export type SortColumn =
  | 'player'
  | 'team'
  | 'position'
  | 'underdog_rank'
  | 'ktc'
  | 'fantasycalc'
  | 'adp'
  | 'market_war'
  | 'my_war'
  | 'delta';

export type SortDirection =
  | 'asc'
  | 'desc';

export type FilterColumn = SortColumn;

export type FilterOperator =
  | 'contains'
  | 'equals'
  | 'gt'
  | 'lt';

export interface TableFilter {
  id: number;
  column: FilterColumn;
  operator: FilterOperator;
  value: string;
}

export type FutureProjectionMode =
  | 'default'
  | 'year';

export const SORT_LABELS: Record<SortColumn, string> = {
  player: 'Player',
  team: 'Team',
  position: 'Position',
  underdog_rank: 'Underdog rank',
  ktc: 'KTC',
  fantasycalc: 'FantasyCalc',
  adp: 'ADP',
  market_war: 'Market dynasty roster WAR',
  my_war: 'My dynasty roster WAR',
  delta: 'Delta',
};

export function getDefaultSortColumn(
  preference: ValueBasis,
): SortColumn {
  if (preference === 'fantasycalc') {
    return 'fantasycalc';
  }

  if (preference === 'adp') {
    return 'adp';
  }

  if (preference === 'ktc') {
    return 'ktc';
  }

  return 'my_war';
}

export function formatMetric(
  value: number | null | undefined,
) {
  if (value == null) {
    return '--';
  }

  return value.toFixed(2);
}

export function formatMarketNumber(
  value: number | null | undefined,
) {
  if (value == null) {
    return '--';
  }

  return Math.round(value).toLocaleString();
}

export function parseUnderdogRank(
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

export function getItemValueByColumn(
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
    case 'adp':
      return item.player.adp_value ?? Number.NEGATIVE_INFINITY;
    case 'market_war':
      return item.market_values.dynasty_roster_war ?? Number.NEGATIVE_INFINITY;
    case 'my_war':
      return item.custom_values.dynasty_roster_war ?? Number.NEGATIVE_INFINITY;
    case 'delta':
      return item.delta_values.dynasty_roster_war ?? Number.NEGATIVE_INFINITY;
  }
}

export function comparePoolItems(
  left: PersonalValuePoolItem,
  right: PersonalValuePoolItem,
  column: SortColumn,
  direction: SortDirection,
) {
  const positionDiff = (
    (CORE_FANTASY_POSITION_ORDER[left.player.position] ?? 99)
    - (CORE_FANTASY_POSITION_ORDER[right.player.position] ?? 99)
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

export function itemMatchesFilter(
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

export function buildNextTableFilter(
  filters: TableFilter[],
): TableFilter {
  const nextId = filters.reduce(
    (maxId, filter) => Math.max(maxId, filter.id),
    0,
  ) + 1;

  return {
    id: nextId,
    column: 'player',
    operator: 'contains',
    value: '',
  };
}

export function buildEmptyOutcome(): PersonalProjectionOutcomeItem {
  return {
    position_rank: 1,
    probability: 100,
  };
}

export function cloneSeasons(
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

export function cloneOutcomes(
  outcomes: PersonalProjectionOutcomeItem[],
) {
  return outcomes.map((outcome) => ({
    ...outcome,
  }));
}

export function getFallbackOutcomes(
  season: PersonalProjectionSeasonItem | undefined,
) {
  if (season?.outcomes.length) {
    return cloneOutcomes(season.outcomes);
  }

  return [
    {
      position_rank:
        season?.default_position_rank ?? 1,
      probability: 100,
    },
  ];
}

export function getDefaultFutureOutcomes(
  seasons: PersonalProjectionSeasonItem[],
  currentSeason: number,
) {
  const futureSeasons = seasons.filter(
    (season) => season.season !== currentSeason,
  );
  const uncustomizedFutureSeason = futureSeasons.find(
    (season) => !season.is_customized,
  );
  const baseFutureSeason = (
    uncustomizedFutureSeason
    ?? futureSeasons[0]
  );

  return getFallbackOutcomes(
    baseFutureSeason,
  );
}

export function getPoolPlayerIds(
  poolItems: PersonalValuePoolItem[],
) {
  return new Set(
    poolItems.map((item) => item.player.player_id),
  );
}


export interface RankableEntry {
  player_id: string;
  primary_rank: number | null;
}

/**
 * Moves the entry at fromIndex to toIndex within the ranked window,
 * then reassigns the window's existing rank values in order so no
 * other players' ranks change.
 */
export function moveRanking(
  entries: RankableEntry[],
  fromIndex: number,
  toIndex: number,
): RankableEntry[] {
  if (
    fromIndex === toIndex
    || fromIndex < 0
    || toIndex < 0
    || fromIndex >= entries.length
    || toIndex >= entries.length
  ) {
    return entries;
  }

  const next = [...entries];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);

  // Owner prefers strict non-e ranks (Gibbs #1, Bijan #2, ...) -
  // renumber ranked entries sequentially after every move; unranked
  // entries stay anchored unchanged.
  let rank = 0;

  return next.map((entry) => {
    if (entry.primary_rank === null) {
      return entry;
    }

    rank += 1;
    return { ...entry, primary_rank: rank };
  });
}
