import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import { AlertTriangle, HandCoins, Search } from 'lucide-react';

import { LoadingState } from '@/components/feedback/LoadingState';
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
      <LoadingState
        label="Loading your leagues..."
        className="waivers-loading-state"
      />
    );
  }

  if (leagues.error) {
    return (
      <div className="empty-state">
        <AlertTriangle size={32} className="empty-state-icon" />
        <p className="empty-state-title">Unable to load leagues</p>
        <p className="empty-state-message">
          Check your Sleeper connection and try again.
        </p>
      </div>
    );
  }

  if (leagues.data.length === 0) {
    return (
      <div className="empty-state">
        <HandCoins size={32} className="empty-state-icon" />
        <p className="empty-state-title">No waiver leagues</p>
        <p className="empty-state-message">
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
            <LoadingState
              label="Calculating available player values..."
              className="waivers-loading-state"
            />
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
            <div className="empty-state">
              <Search size={32} className="empty-state-icon" />
              <p className="empty-state-title">Unable to load players</p>
              <p className="empty-state-message">
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
