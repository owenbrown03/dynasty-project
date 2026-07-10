import {
  LoaderCircle,
  Search,
} from 'lucide-react';
import {
  useEffect,
  useState,
} from 'react';

import { useBulkTradePlayerSearch } from '@/hooks/sleeper/useBulkTrades';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';

import type {
  BulkTradePlayerSearchResult,
} from '@/types';


interface BulkTradePlayerSearchProps {
  selectedPlayer: BulkTradePlayerSearchResult | null;
  onSelectPlayer: (
    player: BulkTradePlayerSearchResult | null,
  ) => void;
}


function formatMarketValue(
  value: number | null,
): string {
  if (value === null) {
    return '—';
  }

  return value.toLocaleString();
}


export const BulkTradePlayerSearch = ({
  selectedPlayer,
  onSelectPlayer,
}: BulkTradePlayerSearchProps) => {
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const {
    data: players,
    loading,
    fetching,
  } = useBulkTradePlayerSearch(
    searchQuery,
  );

  useEffect(() => {
    const timeout = window.setTimeout(
      () => {
        setSearchQuery(
          searchInput.trim(),
        );
      },
      250,
    );

    return () => {
      window.clearTimeout(
        timeout,
      );
    };
  }, [
    searchInput,
  ]);

  const showResults = (
    searchInput.trim().length >= 2
    && !selectedPlayer
  );

  return (
    <section className="bulk-trade-player-search">
      <label className="bulk-trade-search-label">
        <span>
          Player
        </span>

        <div className="bulk-trade-search-input-wrap">
          <Search size={16} />

          <input
            value={searchInput}
            onChange={event => {
              setSearchInput(
                event.target.value,
              );
            }}
            placeholder="Search a player to buy or sell..."
          />

          {
            loading || fetching
              ? (
                <LoaderCircle
                  className="trade-spinner"
                  size={15}
                />
              )
              : null
          }
        </div>
      </label>

      {
        selectedPlayer
          ? (
            <div className="bulk-trade-selected-player">
              <div className="player-with-avatar">
                <PlayerAvatar
                  playerId={selectedPlayer.player_id}
                  name={selectedPlayer.name}
                  size="md"
                />

                <div className="player-with-avatar-copy">
                  <strong>
                    {selectedPlayer.name}
                  </strong>

                  <span>
                    {
                      [
                        selectedPlayer.position,
                        selectedPlayer.team,
                      ]
                        .filter(Boolean)
                        .join(' · ')
                    }
                  </span>
                </div>
              </div>

              <div className="bulk-trade-selected-values">
                <span>
                  KTC {
                    formatMarketValue(
                      selectedPlayer.ktc_value,
                    )
                  }
                </span>

                <span>
                  FC {
                    formatMarketValue(
                      selectedPlayer.fc_value,
                    )
                  }
                </span>
              </div>

              <button
                className="button-secondary"
                onClick={() => {
                  setSearchInput('');
                  setSearchQuery('');
                  onSelectPlayer(
                    null as unknown as BulkTradePlayerSearchResult,
                  );
                }}
              >
                Change
              </button>
            </div>
          )
          : null
      }

      {
        showResults
          ? (
            <div className="bulk-trade-search-results">
              {
                players.length === 0
                && !loading
                && !fetching
                  ? (
                    <span className="bulk-trade-empty-search">
                      No matching players found.
                    </span>
                  )
                  : null
              }

              {
                players.map(player => (
                  <button
                    key={player.player_id}
                    className="bulk-trade-search-result"
                    onClick={() => {
                      onSelectPlayer(
                        player,
                      );

                      setSearchInput(
                        player.name,
                      );
                    }}
                  >
                    <div className="player-with-avatar">
                      <PlayerAvatar
                        playerId={player.player_id}
                        name={player.name}
                        size="sm"
                      />

                      <div className="player-with-avatar-copy">
                        <strong>
                          {player.name}
                        </strong>

                        <span>
                          {
                            [
                              player.position,
                              player.team,
                              player.underdog_position_rank,
                            ]
                              .filter(Boolean)
                              .join(' · ')
                          }
                        </span>
                      </div>
                    </div>

                    <div>
                      <span>
                        KTC {
                          formatMarketValue(
                            player.ktc_value,
                          )
                        }
                      </span>

                      <span>
                        FC {
                          formatMarketValue(
                            player.fc_value,
                          )
                        }
                      </span>
                    </div>
                  </button>
                ))
              }
            </div>
          )
          : null
      }
    </section>
  );
};
