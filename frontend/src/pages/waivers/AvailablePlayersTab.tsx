import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import {
  useAvailableWaiverPlayers,
  useWaiverLeagueOptions,
} from '@/hooks/sleeper/useWaivers';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

import type {
  ValueBasis,
  WaiverAvailablePlayer,
} from '@/types';

import { AvailableLeagueSelector } from './AvailableLeagueSelector';
import { AvailablePlayerClaimModal } from './AvailablePlayerClaimModal';
import { AvailablePlayersTable } from './AvailablePlayersTable';


interface AvailablePlayersTabProps {
  valueBasis: ValueBasis;
}


export const AvailablePlayersTab = ({
  valueBasis,
}: AvailablePlayersTabProps) => {
  const [
    selectedLeagueId,
    setSelectedLeagueId,
  ] = useState<string | undefined>();

  const [
    claimPlayer,
    setClaimPlayer,
  ] = useState<WaiverAvailablePlayer | null>(
    null,
  );

  const {
    canWrite,
  } = useSleeperConnection();

  const leagues = useWaiverLeagueOptions();

  useEffect(() => {
    if (
      !selectedLeagueId
      && leagues.data.length > 0
    ) {
      setSelectedLeagueId(
        leagues.data[0].league_id,
      );
    }
  }, [
    leagues.data,
    selectedLeagueId,
  ]);

  const selectedLeague = useMemo(
    () => (
      leagues.data.find(
        (league) => (
          league.league_id === selectedLeagueId
        ),
      )
    ),
    [
      leagues.data,
      selectedLeagueId,
    ],
  );

  const claimBlockedReason = (
    selectedLeague
    && selectedLeague.roster_spots_available < 0
      ? (
        `This roster is ${
          Math.abs(
            selectedLeague.roster_spots_available,
          )
        } players over capacity. Remove players before claiming.`
      )
      : undefined
  );

  const availablePlayers = useAvailableWaiverPlayers(
    selectedLeagueId,
    valueBasis,
  );

  if (leagues.loading) {
    return (
      <div className="waivers-loading-state">
        Loading your leagues...
      </div>
    );
  }

  if (leagues.error) {
    return (
      <div className="waivers-empty-state">
        <h2>Unable to load waiver leagues.</h2>

        <p>
          Check your Sleeper connection and try again.
        </p>
      </div>
    );
  }

  if (leagues.data.length === 0) {
    return (
      <div className="waivers-empty-state">
        <h2>No waiver leagues found.</h2>

        <p>
          Sync your Sleeper leagues and try again.
        </p>
      </div>
    );
  }

  return (
    <section className="available-players-section">
      <div className="available-players-toolbar">
        <div>
          <h2>
            Available Players
          </h2>

          <p>
            Full available QB, RB, WR, and TE pool,
            sorted by your selected value basis.
          </p>
        </div>

        <AvailableLeagueSelector
          leagues={leagues.data}
          selectedLeagueId={selectedLeagueId}
          onChange={(leagueId) => {
            setSelectedLeagueId(leagueId);
            setClaimPlayer(null);
          }}
        />
      </div>

      {
        availablePlayers.loading
          ? (
            <div className="waivers-loading-state">
              Calculating available player values...
            </div>
          )
          : null
      }

      {
        availablePlayers.fetching
          && !availablePlayers.loading
          ? (
            <div className="waivers-refreshing">
              Updating player values...
            </div>
          )
          : null
      }

      {
        availablePlayers.error
          ? (
            <div className="waivers-empty-state">
              <h2>Unable to load available players.</h2>

              <p>
                Try selecting the league again.
              </p>
            </div>
          )
          : null
      }

      {
        availablePlayers.data
          ? (
            <>
              <div className="available-players-summary">
                <span>
                  {
                    availablePlayers.data.total_players
                      .toLocaleString()
                  }
                  {' '}available players
                </span>

                <span>
                  Ranked by {availablePlayers.data.value_label}
                </span>
              </div>

              <AvailablePlayersTable
                data={availablePlayers.data}
                canWrite={
                  canWrite
                  && !claimBlockedReason
                }
                claimDisabledReason={claimBlockedReason}
                onClaim={setClaimPlayer}
              />
            </>
          )
          : null
      }

      {
        claimPlayer
        && selectedLeague
          ? (
            <AvailablePlayerClaimModal
              league={selectedLeague}
              addPlayer={claimPlayer}
              valueBasis={valueBasis}
              onClose={() => {
                setClaimPlayer(null);
              }}
            />
          )
          : null
      }
    </section>
  );
};