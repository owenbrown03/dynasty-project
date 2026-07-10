import {
  LoaderCircle,
  Search,
} from 'lucide-react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type {
  BulkWaiverPlayerSearchResult,
} from '@/types';

import {
  formatAge,
  formatMarketValue,
} from './waiver.formatters';


interface BulkPlayerSearchProps {
  query: string;
  results: BulkWaiverPlayerSearchResult[];
  loading: boolean;
  selectedPlayerId: string | undefined;

  onQueryChange: (
    value: string,
  ) => void;

  onSelect: (
    player: BulkWaiverPlayerSearchResult,
  ) => void;
}


export const BulkPlayerSearch = ({
  query,
  results,
  loading,
  selectedPlayerId,
  onQueryChange,
  onSelect,
}: BulkPlayerSearchProps) => {
  const showResults = (
    query.trim().length >= 2
  );

  return (
    <section className="bulk-player-search">
      <label className="bulk-search-input">
        <span>Target Player</span>

        <div className="bulk-search-input-wrapper">
          <Search size={16} />

          <input
            value={query}
            placeholder="Search a player..."
            onChange={(event) => {
              onQueryChange(event.target.value);
            }}
          />

          {
            loading
              ? (
                <LoaderCircle
                  className="waiver-spinner"
                  size={15}
                />
              )
              : null
          }
        </div>
      </label>

      {
        showResults
          ? (
            <div className="bulk-search-results">
              {
                !loading
                && results.length === 0
                  ? (
                    <div className="bulk-search-empty">
                      No database players found.
                    </div>
                  )
                  : null
              }

              {
                results.map((player) => (
                  <button
                    key={player.player_id}
                    className={
                      `bulk-search-result ${
                        selectedPlayerId === player.player_id
                          ? 'selected'
                          : ''
                      }`
                    }
                    onClick={() => {
                      onSelect(player);
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
                          {player.position ?? '—'}
                          {' · '}
                          {player.team ?? 'FA'}
                          {' · '}
                          Age {formatAge(player.age)}
                        </span>
                      </div>
                    </div>

                    <div className="bulk-search-market-values">
                      <span>
                        KTC {formatMarketValue(player.ktc_value)}
                      </span>

                      <span>
                        FC {formatMarketValue(player.fc_value)}
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
