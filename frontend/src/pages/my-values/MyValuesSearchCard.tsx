import { LoadingState } from '@/components/feedback/LoadingState';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type { PersonalValueSearchResult } from '@/types';

import {
  formatMarketNumber,
  formatMetric,
} from './myValues.utils';

interface MyValuesSearchCardProps {
  searchTerm: string;
  searchEnabled: boolean;
  loading: boolean;
  fetching: boolean;
  results: PersonalValueSearchResult[];
  onSearchTermChange: (value: string) => void;
  onSelectPlayer: (playerId: string) => void;
}

export function MyValuesSearchCard({
  searchTerm,
  searchEnabled,
  loading,
  fetching,
  results,
  onSearchTermChange,
  onSelectPlayer,
}: MyValuesSearchCardProps) {
  return (
    <div className="my-values-search-card">
      <div className="my-values-panel-header">
        <div>
          <p>Add players</p>
          <h2>Add players missing from the sheet</h2>
        </div>
      </div>

      <div className="my-values-search-controls">
        <label className="my-values-control my-values-control-grow">
          <span>Player search</span>
          <input
            value={searchTerm}
            placeholder="Search player name"
            onChange={(event) => {
              onSearchTermChange(
                event.target.value,
              );
            }}
          />
        </label>
      </div>

      {
        searchEnabled
          ? (
            <div className="my-values-search-results">
              {
                loading || fetching
                  ? (
                    <LoadingState
                      inline
                      label="Searching"
                    />
                  )
                  : results.map((result) => (
                    <button
                      key={result.player_id}
                      type="button"
                      className="my-values-search-result"
                      onClick={() => {
                        onSelectPlayer(
                          result.player_id,
                        );
                      }}
                    >
                      <div className="my-values-pool-player">
                        <PlayerAvatar
                          playerId={result.player_id}
                          name={result.name}
                          size="sm"
                        />
                        <div>
                          <strong>{result.name}</strong>
                          <p>
                            {result.position ?? '--'} · {result.team ?? '--'} · {result.underdog_position_rank ?? 'No UD rank'}
                          </p>
                        </div>
                      </div>

                      <div className="my-values-search-metrics">
                        <span>KTC {result.ktc_value?.toLocaleString() ?? '--'}</span>
                        <span>FC {result.fc_value?.toLocaleString() ?? '--'}</span>
                        <span>ADP {formatMarketNumber(result.adp_value)}</span>
                        <span>WAR {formatMetric(result.dynasty_roster_war)}</span>
                      </div>
                    </button>
                  ))
              }
            </div>
          )
          : (
            <div className="my-values-search-empty">
              Search at least two characters to add players who are missing from the default underdog-backed sheet.
            </div>
          )
      }
    </div>
  );
}
