import {
  Search,
} from 'lucide-react';
import {
  useEffect,
  useState,
} from 'react';

import { useBulkTradePlayerSearch } from '@/hooks/sleeper/useBulkTrades';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { TeamBadge } from '@/components/players/TeamBadge';
import { Skeleton } from '@/components/feedback/Skeleton';

import type {
  BulkTradePlayerSearchResult,
} from '@/types';


interface BulkTradePlayerSearchProps {
  label?: string;
  placeholder?: string;
  selectedPlayers: BulkTradePlayerSearchResult[];
  onAddPlayer: (
    player: BulkTradePlayerSearchResult,
  ) => void;
  onRemovePlayer: (
    playerId: string,
  ) => void;
}

export const BulkTradePlayerSearch = ({
  label = 'Players',
  placeholder = 'Search a player...',
  selectedPlayers,
  onAddPlayer,
  onRemovePlayer,
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
  );

  return (
    <section className="bulk-trade-player-search">
      <label className="bulk-trade-search-label">
        <span>
          {label}
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
            placeholder={placeholder}
          />

          {
            loading || fetching
              ? (
                <Skeleton width={15} height={15} radius={4} />
              )
              : null
          }
        </div>
      </label>

      {
        selectedPlayers.length > 0
          ? (
            <div className="bulk-trade-search-results">
              {
                selectedPlayers.map(player => (
                  <div
                    key={player.player_id}
                    className="bulk-trade-selected-player"
                  >
                    <div className="player-with-avatar">
                      <PlayerAvatar
                        playerId={player.player_id}
                        name={player.name}
                        size="md"
                      />

                      <div className="player-with-avatar-copy">
                        <strong>
                          {player.name}
                        </strong>

                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <span>{player.position}</span>
                          {player.team ? (
                            <>
                              <span>·</span>
                              <TeamBadge team={player.team} size="xs" />
                            </>
                          ) : null}
                        </span>
                      </div>
                    </div>
                    <button
                      className="button-secondary"
                      onClick={() => {
                        onRemovePlayer(
                          player.player_id,
                        );
                      }}
                    >
                      Remove
                    </button>
                  </div>
                ))
              }
            </div>
          )
          : null
      }

      {
        showResults
          ? (
            <div className="bulk-trade-search-results">
              {
                loading || fetching
                  ? (
                    Array.from({ length: 3 }).map((_, index) => (
                      <div
                        className="bulk-trade-search-result bulk-trade-search-result-skeleton"
                        key={index}
                      >
                        <div className="player-with-avatar">
                          <Skeleton width={28} height={28} radius={4} />
                          <div className="player-with-avatar-copy">
                            <Skeleton width={132} variant="title" />
                            <Skeleton width={90} variant="text" />
                          </div>
                        </div>
                      </div>
                    ))
                  )
                  : null
              }

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
                !loading && !fetching
                  ? players.map(player => (
                  <button
                    key={player.player_id}
                    className="bulk-trade-search-result"
                    onClick={() => {
                      onAddPlayer(
                        player,
                      );
                      setSearchInput('');
                      setSearchQuery('');
                    }}
                    disabled={selectedPlayers.some(
                      selectedPlayer => (
                        selectedPlayer.player_id === player.player_id
                      ),
                    )}
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

                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <span>{player.position}</span>
                          {player.team ? (
                            <>
                              <span>·</span>
                              <TeamBadge team={player.team} size="xs" />
                            </>
                          ) : null}
                          {player.underdog_position_rank ? (
                            <>
                              <span>·</span>
                              <span>{player.underdog_position_rank}</span>
                            </>
                          ) : null}
                        </span>
                      </div>
                    </div>

                  </button>
                  ))
                  : null
              }
            </div>
          )
          : null
      }
    </section>
  );
};
