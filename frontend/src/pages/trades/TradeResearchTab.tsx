import { useMemo, useState } from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { TradeCards } from './TradeCards';
import { useTrades } from '@/hooks/sleeper/useTrades';

export const TradeResearchTab = () => {
  const trades = useTrades();
  const [search, setSearch] = useState('');
  const [selectedSettings, setSelectedSettings] = useState<string[]>([]);

  const availableSettings = useMemo(
    () => {
      const unique = new Set<string>();

      trades.data.forEach((trade) => {
        trade.league_settings.forEach((setting) => {
          unique.add(setting);
        });
      });

      return Array.from(unique).sort();
    },
    [trades.data],
  );

  const filteredTrades = useMemo(
    () => {
      const normalizedSearch = search.trim().toLowerCase();

      return trades.data.filter((trade) => {
        const matchesSettings = selectedSettings.every((setting) => (
          trade.league_settings.includes(setting)
        ));

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
      selectedSettings,
      trades.data,
    ],
  );

  if (trades.fetching) {
    return (
      <div className="trades-container">
        <LoadingState label="Fetching trade database..." />
      </div>
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

          {
            availableSettings.length > 0
              ? (
                <div className="trade-research-settings">
                  <span className="trade-research-settings-label">
                    League settings
                  </span>

                  <div className="trade-research-setting-chips">
                    {
                      availableSettings.map((setting) => {
                        const active = selectedSettings.includes(
                          setting,
                        );

                        return (
                          <button
                            key={setting}
                            type="button"
                            className={
                              active
                                ? 'trade-research-setting-chip active'
                                : 'trade-research-setting-chip'
                            }
                            onClick={() => {
                              setSelectedSettings((current) => (
                                current.includes(setting)
                                  ? current.filter((item) => item !== setting)
                                  : [...current, setting]
                              ));
                            }}
                          >
                            {setting}
                          </button>
                        );
                      })
                    }
                  </div>
                </div>
              )
              : null
          }
        </section>

        <div className="trade-research-summary">
          Showing {filteredTrades.length} of {trades.data.length} trades
        </div>

        {
          filteredTrades.length > 0
            ? <TradeCards trades={filteredTrades} />
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
