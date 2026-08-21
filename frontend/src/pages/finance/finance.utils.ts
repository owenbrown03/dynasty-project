import type {
  FinanceDefaultSettings,
  FinanceLeagueSeasonEntry,
  FinancePlacePayout,
} from '@/types';

export type FinanceDraftRow = {
  place: string;
  amount: string;
};

export type FinanceSettingsDraft = {
  buyInAmount: string;
  payoutStructure: FinanceDraftRow[];
};

export type FinanceSeasonDraft = FinanceSettingsDraft & {
  isExcluded: boolean;
};

export type FinanceChartEntry = {
  key: string;
  label: string;
  subLabel: string;
  winningsAmount: number;
  projectedWinningsAmount: number;
  netAmount: number;
  isProjected: boolean;
};

export type FinanceTimelinePoint = {
  week: number;
  label: string;
  actualAmount: number | null;
  projectedAmount: number;
};

export function formatCurrency(
  value: number,
) {
  const rounded = Math.round(value);
  const normalizedValue = Object.is(rounded, -0) || rounded === 0 ? 0 : value;

  return new Intl.NumberFormat(
    'en-US',
    {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    },
  ).format(normalizedValue);
}

export function ordinal(
  value: number,
) {
  const mod10 = value % 10;
  const mod100 = value % 100;

  if (mod10 === 1 && mod100 !== 11) {
    return `${value}st`;
  }

  if (mod10 === 2 && mod100 !== 12) {
    return `${value}nd`;
  }

  if (mod10 === 3 && mod100 !== 13) {
    return `${value}rd`;
  }

  return `${value}th`;
}

export function parseAmount(
  value: string,
) {
  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed
    : 0;
}

export function parseNullableAmount(
  value: string,
) {
  const trimmed = value.trim();

  if (!trimmed) {
    return null;
  }

  const parsed = Number(trimmed);
  return Number.isFinite(parsed)
    ? parsed
    : null;
}

export function getDraftKey(
  entry: FinanceLeagueSeasonEntry,
) {
  return `${entry.league_id}-${entry.season}`;
}

export function buildPayoutRows(
  payouts: FinancePlacePayout[],
) {
  if (!payouts.length) {
    return [
      {
        place: '1',
        amount: '',
      },
    ];
  }

  return payouts.map((payout) => ({
    place: payout.place.toString(),
    amount: payout.amount
      ? payout.amount.toString()
      : '',
  }));
}

export function buildSettingsDraft(
  settings: FinanceDefaultSettings | {
    buy_in_amount: number | null;
    payout_structure: FinancePlacePayout[];
  },
) {
  return {
    buyInAmount: settings.buy_in_amount?.toString() ?? '',
    payoutStructure: buildPayoutRows(
      settings.payout_structure,
    ),
  };
}

export function buildSeasonDrafts(
  entries: FinanceLeagueSeasonEntry[],
) {
  return Object.fromEntries(
    entries.map((entry) => [
      getDraftKey(entry),
      {
        buyInAmount: entry.buy_in_amount.toString(),
        payoutStructure: buildPayoutRows(
          entry.payout_structure,
        ),
        isExcluded: entry.is_excluded,
      },
    ]),
  ) as Record<string, FinanceSeasonDraft>;
}

export function normalizeDraftRows(
  rows: FinanceDraftRow[],
) {
  return rows
    .map((row) => ({
      place: parseAmount(row.place).toString(),
      amount: row.amount,
    }))
    .filter((row) => parseAmount(row.place) > 0)
    .sort((left, right) => (
      parseAmount(left.place) - parseAmount(right.place)
    ));
}

export function draftRowsEqual(
  left: FinanceDraftRow[],
  right: FinanceDraftRow[],
) {
  const leftRows = normalizeDraftRows(left);
  const rightRows = normalizeDraftRows(right);

  if (leftRows.length !== rightRows.length) {
    return false;
  }

  return leftRows.every((row, index) => (
    row.place === rightRows[index].place
    && parseAmount(row.amount) === parseAmount(rightRows[index].amount)
  ));
}

export function addPayoutRow(
  draft: FinanceSettingsDraft,
) {
  const nextPlace = (
    draft.payoutStructure.length
      ? Math.max(
          ...draft.payoutStructure.map((row) => (
            parseAmount(row.place)
          )),
        ) + 1
      : 1
  );

  return {
    ...draft,
    payoutStructure: [
      ...draft.payoutStructure,
      {
        place: nextPlace.toString(),
        amount: '',
      },
    ],
  };
}

export function sourceLabel(
  source: string,
) {
  switch (source) {
    case 'season_override':
      return 'Season override';
    case 'league_default':
      return 'League default';
    case 'global_default':
      return 'Global default';
    case 'commissioner_dues':
      return 'Commissioner dues';
    default:
      return 'Not set';
  }
}

export function projectionSourceLabel(
  source: FinanceLeagueSeasonEntry['projected_winnings_source'],
) {
  switch (source) {
    case 'seed_probability':
      return 'Seed probability';
    case 'historical_rank':
      return 'Historical finish';
    case 'configured_place':
      return 'Configured place';
    case 'no_projection':
      return 'No projection';
    default:
      return 'Heuristic';
  }
}

export function financeResultLabel(
  entry: FinanceLeagueSeasonEntry,
) {
  if (entry.finish_place !== null) {
    return `Finish ${ordinal(entry.finish_place)} of ${entry.total_rosters}`;
  }

  if (entry.projected_finish_place !== null) {
    return `Projected seed ${ordinal(entry.projected_finish_place)} of ${entry.total_rosters}`;
  }

  if (entry.rank !== null) {
    return `Current rank ${ordinal(entry.rank)} of ${entry.total_rosters}`;
  }

  return `${entry.total_rosters} teams`;
}

export function isFinanceSeasonComplete(
  entry: FinanceLeagueSeasonEntry,
) {
  return entry.status === 'complete';
}

export function effectiveFinanceWinnings(
  entry: FinanceLeagueSeasonEntry,
) {
  return isFinanceSeasonComplete(entry)
    ? entry.winnings_amount
    : entry.projected_winnings_amount;
}

export function effectiveFinanceNet(
  entry: FinanceLeagueSeasonEntry,
) {
  return effectiveFinanceWinnings(entry) - entry.buy_in_amount;
}

export function buildSeasonChartEntries(
  entries: FinanceLeagueSeasonEntry[],
): FinanceChartEntry[] {
  const bySeason = new Map<
    string,
    {
      winningsAmount: number;
      projectedWinningsAmount: number;
      netAmount: number;
      leagueCount: number;
      projectedCount: number;
    }
  >();

  for (const entry of entries) {
    const current = bySeason.get(entry.season) ?? {
      winningsAmount: 0,
      projectedWinningsAmount: 0,
      netAmount: 0,
      leagueCount: 0,
      projectedCount: 0,
    };

    current.winningsAmount += effectiveFinanceWinnings(entry);
    current.projectedWinningsAmount += entry.projected_winnings_amount;
    current.netAmount += effectiveFinanceNet(entry);
    current.leagueCount += 1;
    if (!isFinanceSeasonComplete(entry)) {
      current.projectedCount += 1;
    }

    bySeason.set(entry.season, current);
  }

  return Array.from(bySeason.entries())
    .map(([season, totals]) => ({
      key: season,
      label: season,
      subLabel: `${totals.leagueCount} ${
        totals.leagueCount === 1 ? 'league' : 'leagues'
      }${totals.projectedCount > 0 ? ' · projected' : ''}`,
      winningsAmount: totals.winningsAmount,
      projectedWinningsAmount: totals.projectedWinningsAmount,
      netAmount: totals.netAmount,
      isProjected: totals.projectedCount > 0,
    }))
    .sort((left, right) => (
      Number(left.label) - Number(right.label)
    ));
}

export function buildCurrentFinanceTimeline(
  entries: FinanceLeagueSeasonEntry[],
): FinanceTimelinePoint[] {
  if (!entries.length) {
    return [];
  }

  return [
    {
      week: 1,
      label: 'Week 1',
      actualAmount: entries.reduce(
        (sum, entry) => sum + effectiveFinanceWinnings(entry),
        0,
      ),
      projectedAmount: entries.reduce(
        (sum, entry) => sum + entry.projected_winnings_amount,
        0,
      ),
    },
  ];
}
