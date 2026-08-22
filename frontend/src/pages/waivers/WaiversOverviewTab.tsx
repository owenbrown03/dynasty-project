import { AlertTriangle, HandCoins, WifiOff } from 'lucide-react';
import { Skeleton } from '@/components/feedback/Skeleton';
import { useWaiverOverview } from '@/hooks/sleeper/useWaivers';

import type { ValueBasis } from '@/types';

import { WaiverLeagueCard } from './WaiverLeagueCard';


interface WaiversOverviewTabProps {
  valueBasis: ValueBasis;
  onOpenAvailableLeague: (
    leagueId: string,
  ) => void;
}

function WaiverOverviewSkeleton() {
  return (
    <section
      className="waiver-league-list"
      role="status"
      aria-live="polite"
    >
      <span className="skeleton-sr-label">Loading waiver recommendations...</span>
      {
        Array.from({ length: 4 }).map((_, index) => (
          <article className="waiver-league-card" key={index}>
            <div className="waiver-league-header">
              <div className="waiver-league-identity">
                <Skeleton width={40} height={40} radius={4} />
                <div>
                  <Skeleton width={190} variant="title" />
                  <Skeleton width={150} variant="text" />
                </div>
              </div>

              <div className="waiver-gain">
                <Skeleton width={72} variant="text" />
                <Skeleton width={82} height={30} />
              </div>
            </div>

            <div className="waiver-league-stats">
              {
                Array.from({ length: 4 }).map((__, statIndex) => (
                  <div className="waiver-stat" key={statIndex}>
                    <Skeleton width={15} height={15} radius={4} />
                    <Skeleton width={82} variant="text" />
                    <Skeleton width={56} height={20} />
                  </div>
                ))
              }
            </div>

            <div className="waiver-recommendation-grid">
              {
                Array.from({ length: 2 }).map((__, recommendationIndex) => (
                  <div
                    className="waiver-player-card waiver-recommendation-skeleton"
                    key={recommendationIndex}
                  >
                    <Skeleton width={112} variant="text" />
                    <Skeleton width={42} height={42} radius={4} />
                    <Skeleton width={150} variant="title" />
                    <Skeleton width={96} variant="text" />
                  </div>
                ))
              }
            </div>
          </article>
        ))
      }
    </section>
  );
}


export const WaiversOverviewTab = ({
  valueBasis,
  onOpenAvailableLeague,
}: WaiversOverviewTabProps) => {
  const cheapWaivers = useWaiverOverview(valueBasis, true);
  const fullWaivers = useWaiverOverview(valueBasis, false);

  const displayData = fullWaivers.data ?? cheapWaivers.data;
  const isLoading = cheapWaivers.loading;
  const isFetching = fullWaivers.fetching;
  const hasError = fullWaivers.error || cheapWaivers.error;

  const waivers = {
    loading: isLoading,
    fetching: isFetching,
    error: hasError,
    data: displayData,
  };

  if (waivers.loading) {
    return (
      <WaiverOverviewSkeleton />
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
