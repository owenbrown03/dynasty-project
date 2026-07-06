import { useWaiverOverview } from '@/hooks/sleeper/useWaivers';

import type { ValueBasis } from '@/types';

import { WaiverLeagueCard } from './WaiverLeagueCard';


interface WaiversOverviewTabProps {
  valueBasis: ValueBasis;
}


export const WaiversOverviewTab = ({
  valueBasis,
}: WaiversOverviewTabProps) => {
  const waivers = useWaiverOverview(valueBasis);

  if (waivers.loading) {
    return (
      <div className="waivers-loading-state">
        Loading waiver recommendations...
      </div>
    );
  }

  if (waivers.error) {
    return (
      <div className="waivers-empty-state">
        <h2>Unable to load waiver recommendations.</h2>

        <p>
          Check your Sleeper connection and try again.
        </p>
      </div>
    );
  }

  if (!waivers.data) {
    return (
      <div className="waivers-empty-state">
        <h2>Connect your Sleeper account.</h2>

        <p>
          Waiver recommendations appear after your
          Sleeper account is connected.
        </p>
      </div>
    );
  }

  if (waivers.data.leagues.length === 0) {
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
            />
          ))
        }
      </section>
    </>
  );
};