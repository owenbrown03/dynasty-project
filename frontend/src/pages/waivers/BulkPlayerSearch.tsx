import {
  Search,
} from 'lucide-react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { TeamBadge } from '@/components/players/TeamBadge';
import { Skeleton } from '@/components/feedback/Skeleton';
import type {
  BulkWaiverPlayerSearchResult,
} from '@/types';

import {
  formatAge,
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
                <Skeleton width={15} height={15} radius={4} />
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
                loading
                  ? (
                    Array.from({ length: 3 }).map((_, index) => (
                      <div className="bulk-search-result bulk-search-result-skeleton" key={index}>
                        <div className="player-with-avatar">
                          <Skeleton width={28} height={28} radius={4} />
                          <div className="player-with-avatar-copy">
                            <Skeleton width={140} variant="title" />
                            <Skeleton width={120} variant="text" />
                          </div>
                        </div>
                      </div>
                    ))
                  )
                  : null
              }

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
                !loading
                  ? results.map((player) => (
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

                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <span>{player.position ?? '—'}</span>
                          {player.team ? (
                            <>
                              <span>·</span>
                              <TeamBadge team={player.team} size="xs" />
                            </>
                          ) : null}
                          <span>·</span>
                          <span>Age {formatAge(player.age)}</span>
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
