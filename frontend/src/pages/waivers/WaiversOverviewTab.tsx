import { AlertTriangle, HandCoins, WifiOff } from 'lucide-react';
import { LoadingState } from '@/components/feedback/LoadingState';
import { useWaiverOverview } from '@/hooks/sleeper/useWaivers';

import type { ValueBasis } from '@/types';

import { WaiverLeagueCard } from './WaiverLeagueCard';


interface WaiversOverviewTabProps {
  valueBasis: ValueBasis;
  onOpenAvailableLeague: (
    leagueId: string,
  ) => void;
}


export const WaiversOverviewTab = ({
  valueBasis,
  onOpenAvailableLeague,
}: WaiversOverviewTabProps) => {
  const waivers = useWaiverOverview(valueBasis);

  if (waivers.loading) {
    return (
      <LoadingState
        label="Loading waiver recommendations..."
        className="waivers-loading-state"
      />
    );
  }

  if (waivers.error) {
    return (
      <div className="empty-state">
        <AlertTriangle size={32} className="empty-state-icon" />
        <p className="empty-state-title">Unable to load recommendations</p>
        <p className="empty-state-message">
          Check your Sleeper connection and try again.
        </p>
      </div>
    );
  }

  if (!waivers.data) {
    return (
      <div className="empty-state">
        <WifiOff size={32} className="empty-state-icon" />
        <p className="empty-state-title">Connect your Sleeper account</p>
        <p className="empty-state-message">
          Waiver recommendations appear after your
          Sleeper account is connected.
        </p>
      </div>
    );
  }

  if (waivers.data.leagues.length === 0) {
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
    <>
      {
        waivers.fetching
          ? (
            <div className="waivers-refreshing">
              Updating recommendations...
            </div>
          )
          : null
      }

      <section className="waiver-league-list">
        {
          waivers.data.leagues.map((league) => (
            <WaiverLeagueCard
              key={league.league_id}
              league={league}
              onOpenAvailableLeague={
                onOpenAvailableLeague
              }
            />
          ))
        }
      </section>
    </>
  );
};
