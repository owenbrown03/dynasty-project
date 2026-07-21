import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import { PaginationToolbar } from '@/components/controls/PaginationToolbar';
import { Skeleton } from '@/components/feedback/Skeleton';
import { TradeCards } from './TradeCards';
import { useTrades } from '@/hooks/sleeper/useTrades';

type TradeSettingsFilterKey =
  | 'lineup'
  | 'teams'
  | 'starters'
  | 'roster'
  | 'qbFormat'
  | 'ppr'
  | 'pptd'
  | 'tep';

type TradeSettingsFilters = Record<
  TradeSettingsFilterKey,
  string
>;

type TradeSettingsOption = {
  value: string;
  label: string;
};

type TradeSettingsFilterGroup = {
  key: TradeSettingsFilterKey;
  label: string;
  options: TradeSettingsOption[];
};

const DEFAULT_FILTERS: TradeSettingsFilters = {
  lineup: '',
  teams: '',
  starters: '',
  roster: '',
  qbFormat: '',
  ppr: '',
  pptd: '',
  tep: '',
};

const FILTER_KEYS: TradeSettingsFilterKey[] = [
  'lineup',
  'teams',
  'starters',
  'roster',
  'qbFormat',
  'ppr',
  'pptd',
  'tep',
];

function TradeResearchSkeleton() {
  return (
    <div
      className="trades-container trade-research-skeleton"
      role="status"
      aria-live="polite"
    >
      <span className="skeleton-sr-label">Fetching trade database...</span>

      <div className="trades-section-header">
        <div>
          <Skeleton width={74} variant="text" />
          <Skeleton width={190} variant="title" />
          <Skeleton width="min(520px, 100%)" variant="text" />
        </div>
      </div>

      <section className="trade-research-filters">
        <Skeleton height={42} />
        <div className="trade-research-settings">
          <div className="trade-research-settings-header">
            <Skeleton width={120} variant="text" />
            <Skeleton width={110} height={38} />
          </div>
          <div className="trade-research-filter-grid">
            {
              Array.from({ length: 6 }).map((_, index) => (
                <label className="trade-research-filter-control" key={index}>
                  <Skeleton width={70} variant="text" />
                  <Skeleton height={38} />
                </label>
              ))
            }
          </div>
        </div>
      </section>

      <Skeleton width={160} variant="text" />

      <div className="trade-cards">
        {
          Array.from({ length: 4 }).map((_, index) => (
            <article className="trade-card trade-card-skeleton" key={index}>
              <header className="trade-header">
                <div className="trade-header-main">
                  <div className="trade-league-identity">
                    <Skeleton width={34} height={34} radius={4} />
                    <div>
                      <Skeleton width={56} variant="text" />
                      <Skeleton width={180} variant="title" />
                    </div>
                  </div>

                  <div className="trade-league-settings">
                    {
                      Array.from({ length: 5 }).map((__, settingIndex) => (
                        <Skeleton width={64} height={22} key={settingIndex} />
                      ))
                    }
                  </div>
                </div>

                <Skeleton width={128} variant="text" />
              </header>

              <div className="trade-users-row">
                {
                  Array.from({ length: 2 }).map((__, sideIndex) => (
                    <div className="user-card" key={sideIndex}>
                      <header className="user-header">
                        <div className="player-with-avatar">
                          <Skeleton width={28} height={28} radius={4} />
                          <Skeleton width={120} variant="title" />
                        </div>
                      </header>

                      <div className="adds">
                        {
                          Array.from({ length: 2 }).map((___, assetIndex) => (
                            <div className="movement-row" key={`add-${assetIndex}`}>
                              <Skeleton width={160} variant="text" />
                            </div>
                          ))
                        }
                      </div>

                      <div className="drops">
                        <div className="movement-row">
                          <Skeleton width={132} variant="text" />
                        </div>
                      </div>
                    </div>
                  ))
                }
              </div>
            </article>
          ))
        }
      </div>
    </div>
  );
}

function parseTradeSettingBadge(
  setting: string,
): {
  key: TradeSettingsFilterKey;
  value: string;
  label: string;
} | null {
  if (setting === 'Best Ball' || setting === 'Lineup') {
    return {
      key: 'lineup',
      value: setting,
      label: setting,
    };
  }

  if (setting === 'SF' || setting === '1QB') {
    return {
      key: 'qbFormat',
      value: setting,
      label: setting === 'SF'
        ? 'Superflex'
        : '1QB',
    };
  }

  const teamsMatch = setting.match(
    /^(\d+)\s+Team$/i,
  );
  if (teamsMatch) {
    return {
      key: 'teams',
      value: teamsMatch[1],
      label: `${teamsMatch[1]} teams`,
    };
  }

  const startersMatch = setting.match(
    /^Start\s+(\d+)$/i,
  );
  if (startersMatch) {
    return {
      key: 'starters',
      value: startersMatch[1],
      label: `Start ${startersMatch[1]}`,
    };
  }

  const rosterMatch = setting.match(
    /^(\d+)\s+Roster$/i,
  );
  if (rosterMatch) {
    return {
      key: 'roster',
      value: rosterMatch[1],
      label: `${rosterMatch[1]} roster`,
    };
  }

  const pprMatch = setting.match(
    /^([0-9.]+)\s+PPR$/i,
  );
  if (pprMatch) {
    return {
      key: 'ppr',
      value: pprMatch[1],
      label: `${pprMatch[1]} PPR`,
    };
  }

  const pptdMatch = setting.match(
    /^([0-9.]+)\s+PPTD$/i,
  );
  if (pptdMatch) {
    return {
      key: 'pptd',
      value: pptdMatch[1],
      label: `${pptdMatch[1]} pass TD`,
    };
  }

  const tepMatch = setting.match(
    /^([0-9.]+)\s+TEP$/i,
  );
  if (tepMatch) {
    return {
      key: 'tep',
      value: tepMatch[1],
      label: `${tepMatch[1]} TEP`,
    };
  }

  return null;
}

function getTradeSettingsFilterValue(
  settings: string[],
  filterKey: TradeSettingsFilterKey,
): string {
  if (filterKey === 'tep') {
    const parsedTep = settings
      .map(parseTradeSettingBadge)
      .find((item) => item?.key === 'tep');

    return parsedTep?.value ?? '0';
  }

  const parsed = settings
    .map(parseTradeSettingBadge)
    .find((item) => item?.key === filterKey);

  return parsed?.value ?? '';
}

export const TradeResearchTab = () => {
  const trades = useTrades();
  const [search, setSearch] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<TradeSettingsFilters>(
    DEFAULT_FILTERS,
  );
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const availableFilterGroups = useMemo<TradeSettingsFilterGroup[]>(
    () => {
      const optionsByGroup = new Map<
        TradeSettingsFilterKey,
        Map<string, string>
      >(
        FILTER_KEYS.map(
          key => [
            key,
            new Map<string, string>(),
          ],
        ),
      );

      trades.data.forEach((trade) => {
        trade.league_settings.forEach((setting) => {
          const parsed = parseTradeSettingBadge(
            setting,
          );

          if (!parsed) {
            return;
          }

          optionsByGroup.get(
            parsed.key,
          )?.set(
            parsed.value,
            parsed.label,
          );
        });

        optionsByGroup.get('tep')?.set(
          '0',
          'No TEP',
        );
      });

      const groups: Array<{
        key: TradeSettingsFilterKey;
        label: string;
      }> = [
        {
          key: 'lineup',
          label: 'Format',
        },
        {
          key: 'teams',
          label: 'Teams',
        },
        {
          key: 'starters',
          label: 'Starters',
        },
        {
          key: 'roster',
          label: 'Roster size',
        },
        {
          key: 'qbFormat',
          label: 'QB format',
        },
        {
          key: 'ppr',
          label: 'PPR',
        },
        {
          key: 'pptd',
          label: 'Pass TD',
        },
        {
          key: 'tep',
          label: 'TE Premium',
        },
      ];

      return groups.map((group) => {
        const optionMap = optionsByGroup.get(
          group.key,
        ) ?? new Map<string, string>();

        const options = Array.from(
          optionMap.entries(),
        )
          .sort(
            (left, right) => (
              left[1].localeCompare(right[1], undefined, {
                numeric: true,
              })
            ),
          )
          .map(
            ([value, label]) => ({
              value,
              label,
            }),
          );

        return {
          key: group.key,
          label: group.label,
          options,
        };
      }).filter(
        group => group.options.length > 1,
      );
    },
    [trades.data],
  );

  const filteredTrades = useMemo(
    () => {
      const normalizedSearch = search.trim().toLowerCase();

      return trades.data.filter((trade) => {
        const matchesSettings = Object.entries(
          selectedFilters,
        ).every(([key, selectedValue]) => {
          if (!selectedValue) {
            return true;
          }

          return getTradeSettingsFilterValue(
            trade.league_settings,
            key as TradeSettingsFilterKey,
          ) === selectedValue;
        });

        if (!matchesSettings) {
          return false;
        }

        if (!normalizedSearch) {
          return true;
        }

        const haystack = [
          trade.league_name,
          ...trade.league_settings,
          ...trade.users.flatMap((user) => [
            user.display_name,
            ...user.adds.map((movement) => movement.name),
            ...user.drops.map((movement) => movement.name),
          ]),
        ]
          .join(' ')
          .toLowerCase();

        return haystack.includes(
          normalizedSearch,
        );
      });
    },
    [
      search,
      selectedFilters,
      trades.data,
    ],
  );

  const totalPages = Math.max(
    1,
    Math.ceil(
      filteredTrades.length / pageSize,
    ),
  );

  useEffect(() => {
    setPage(1);
  }, [
    pageSize,
    search,
    selectedFilters,
  ]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [
    page,
    totalPages,
  ]);

  const paginatedTrades = useMemo(
    () => {
      const startIndex = (page - 1) * pageSize;
      return filteredTrades.slice(
        startIndex,
        startIndex + pageSize,
      );
    },
    [
      filteredTrades,
      page,
      pageSize,
    ],
  );

  if (trades.fetching) {
    return (
      <TradeResearchSkeleton />
    );
  }

  if (Array.isArray(trades.data) && trades.data.length > 0) {
    return (
      <div className="trades-container">
        <div className="trades-section-header">
          <div>
            <p className="page-eyebrow">Research</p>
            <h2 className="trades-section-title">Trade database</h2>
            <p className="page-description">
              Latest actionable trades from your synced Sleeper trade history, filtered by league settings and asset search.
            </p>
          </div>
        </div>

        <section className="trade-research-filters">
          <label className="bulk-trade-search-label">
            <span>Search trades</span>
            <div className="bulk-trade-search-input-wrap">
              <input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                }}
                placeholder="League, manager, or asset"
              />
            </div>
          </label>

          <div className="trade-research-settings">
            <div className="trade-research-settings-header">
              <span className="trade-research-settings-label">
                League settings
              </span>

              <button
                type="button"
                className="button-secondary"
                onClick={() => {
                  setSelectedFilters(
                    DEFAULT_FILTERS,
                  );
                }}
              >
                Reset filters
              </button>
            </div>

            {
              availableFilterGroups.length > 0
                ? (
                  <div className="trade-research-filter-grid">
                    {
                      availableFilterGroups.map((group) => (
                        <label
                          key={group.key}
                          className="trade-research-filter-control"
                        >
                          <span>
                            {group.label}
                          </span>

                          <select
                            value={selectedFilters[group.key]}
                            onChange={(event) => {
                              const nextValue = event.target.value;
                              setSelectedFilters((current) => ({
                                ...current,
                                [group.key]: nextValue,
                              }));
                            }}
                          >
                            <option value="">
                              All
                            </option>

                            {
                              group.options.map((option) => (
                                <option
                                  key={`${group.key}-${option.value}`}
                                  value={option.value}
                                >
                                  {option.label}
                                </option>
                              ))
                            }
                          </select>
                        </label>
                      ))
                    }
                  </div>
                )
                : null
            }
          </div>
        </section>

        <div className="trade-research-summary">
          Showing {filteredTrades.length} of {trades.data.length} trades
        </div>

        {
          filteredTrades.length > 0
            ? (
              <PaginationToolbar
                page={page}
                pageSize={pageSize}
                totalPages={totalPages}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
              />
            )
            : null
        }

        {
          filteredTrades.length > 0
            ? <TradeCards trades={paginatedTrades} />
            : (
              <p className="no-results-text">
                No trades matched the current filters.
              </p>
            )
        }
      </div>
    );
  }

  return (
    <div className="trades-container">
      {trades.username ? (
        <p className="no-results-text">No transaction history found for "{trades.username}".</p>
      ) : (
        <p className="no-results-text">Please enter a username to search trades.</p>
      )}
    </div>
  );
};
