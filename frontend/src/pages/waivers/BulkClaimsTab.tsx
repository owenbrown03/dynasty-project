import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import {
  useBulkWaiverAvailability,
  useBulkWaiverPlayerSearch,
  useSubmitBulkWaiverClaims,
} from '@/hooks/sleeper/useWaivers';

import type {
  BulkWaiverLeagueAvailability,
  BulkWaiverPlayerSearchResult,
  ValueBasis,
  WaiverClaimRequest,
} from '@/types';

import { BulkClaimLeagueRow } from './BulkClaimLeagueRow';
import { BulkClaimReviewModal } from './BulkClaimReviewModal';
import { BulkPlayerSearch } from './BulkPlayerSearch';


interface BulkClaimsTabProps {
  valueBasis: ValueBasis;
}


export const BulkClaimsTab = ({
  valueBasis,
}: BulkClaimsTabProps) => {
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const [selectedPlayer, setSelectedPlayer] = useState<
    BulkWaiverPlayerSearchResult | undefined
  >();

  const [claimsByLeagueId, setClaimsByLeagueId] = useState<
    Record<string, WaiverClaimRequest>
  >({});

  const [showReview, setShowReview] = useState(false);

  const {
    canWrite,
  } = useSleeperConnection();

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setSearchQuery(searchInput);
    }, 300);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [
    searchInput,
  ]);

  const search = useBulkWaiverPlayerSearch(
    searchQuery,
  );

  const availability = useBulkWaiverAvailability(
    selectedPlayer?.player_id,
    valueBasis,
  );

  const bulkSubmit = useSubmitBulkWaiverClaims();

  const selectedClaims = useMemo(
    () => Object.values(claimsByLeagueId),
    [claimsByLeagueId],
  );

  const leagueNamesById = useMemo(
    () => Object.fromEntries(
      availability.data?.leagues.map((league) => [
        league.league_id,
        league.league_name,
      ])
      ?? [],
    ),
    [availability.data],
  );

  const handlePlayerSelect = (
    player: BulkWaiverPlayerSearchResult,
  ) => {
    setSelectedPlayer(player);
    setClaimsByLeagueId({});
    setShowReview(false);
    bulkSubmit.reset();
  };

  const handleToggleLeague = (
    league: BulkWaiverLeagueAvailability,
  ) => {
    setClaimsByLeagueId((current) => {
      const existing = current[league.league_id];

      if (existing) {
        const {
          [league.league_id]: _removed,
          ...rest
        } = current;

        return rest;
      }

      return {
        ...current,

        [league.league_id]: {
          league_id: league.league_id,
          roster_id: league.roster_id,

          add_player_id: (
            selectedPlayer?.player_id ?? ''
          ),

          drop_player_id: (
            league.requires_drop
              ? (
                league.recommended_drop?.player_id
                ?? null
              )
              : null
          ),

          bid: 0,
        },
      };
    });
  };

  const handleClaimChange = (
    claim: WaiverClaimRequest,
  ) => {
    setClaimsByLeagueId((current) => ({
      ...current,
      [claim.league_id]: claim,
    }));
  };

  const handleSubmit = async () => {
    if (selectedClaims.length === 0) {
      return;
    }

    await bulkSubmit.submitBulkClaimsAsync({
      claims: selectedClaims,
    });
  };
  
  const availabilityData = availability.data;

  return (
    <section className="bulk-claims-section">
      <div className="bulk-claims-toolbar">
        <div>
          <h2>Bulk Claims</h2>

          <p>
            Search one player and submit claims in every
            league where they are available.
          </p>
        </div>

        {
          !canWrite
            ? (
              <span className="bulk-write-warning">
                Enable Sleeper write access to submit claims
              </span>
            )
            : null
        }
      </div>

      <BulkPlayerSearch
        query={searchInput}
        results={search.data}
        loading={search.fetching}
        selectedPlayerId={selectedPlayer?.player_id}
        onQueryChange={setSearchInput}
        onSelect={handlePlayerSelect}
      />

      {
        selectedPlayer
          ? (
            <div className="bulk-selected-player">
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
                  {selectedPlayer.position ?? '—'}
                  {' · '}
                  {selectedPlayer.team ?? 'FA'}
                </span>
              </div>
            </div>
          )
          : null
      }

      {
        availability.loading
          ? (
            <div className="waivers-loading-state">
              Checking availability across your leagues...
            </div>
          )
          : null
      }

      {
        availability.error
          ? (
            <div className="waivers-empty-state">
              <h2>Unable to check league availability.</h2>

              <p>
                Try selecting the player again.
              </p>
            </div>
          )
          : null
      }

      {
        availabilityData
          ? (
            <>
              <div className="bulk-availability-summary">
                <span>
                  {
                    availabilityData.leagues.filter(
                      (league) => league.is_available,
                    ).length
                  }
                  {' '}available leagues
                </span>

                <span>
                  Ranked by {availabilityData.value_label}
                </span>
              </div>

              <div className="bulk-claim-league-list">
                {
                  availabilityData.leagues.map(
                    (league) => (
                      <BulkClaimLeagueRow
                        key={league.league_id}
                        targetPlayerId={
                          selectedPlayer?.player_id
                          ?? availabilityData.player.player_id
                        }
                        targetPlayerName={
                          selectedPlayer?.name
                          ?? availabilityData.player.name
                        }
                        league={league}
                        valueBasis={valueBasis}
                        draftClaim={
                          claimsByLeagueId[
                            league.league_id
                          ]
                        }
                        canWrite={canWrite}
                        onToggle={handleToggleLeague}
                        onChange={handleClaimChange}
                      />
                    ),
                  )
                }
              </div>

              {
                selectedClaims.length > 0
                  ? (
                    <div className="bulk-submit-bar">
                      <span>
                        {selectedClaims.length}
                        {' '}claim{
                          selectedClaims.length === 1
                            ? ''
                            : 's'
                        } selected
                      </span>

                      <button
                        className="button-secondary waiver-modal-submit-button"
                        onClick={() => {
                          setShowReview(true);
                        }}
                        disabled={!canWrite}
                      >
                        Review Claims
                      </button>
                    </div>
                  )
                  : null
              }
            </>
          )
          : null
      }
      {
        showReview
        && selectedPlayer
          ? (
            <BulkClaimReviewModal
              player={selectedPlayer}
              claims={selectedClaims}
              leagueNamesById={leagueNamesById}
              submitting={bulkSubmit.submitting}
              result={bulkSubmit.data}
              error={bulkSubmit.error}
              onClose={() => {
                setShowReview(false);

                if (bulkSubmit.data) {
                  setClaimsByLeagueId({});
                  bulkSubmit.reset();
                }
              }}
              onSubmit={handleSubmit}
            />
          )
          : null
      }
    </section>
  );
};
