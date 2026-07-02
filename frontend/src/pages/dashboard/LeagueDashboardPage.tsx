import './LeagueDashboardPage.css';

import { UsernameInput } from './UsernameInput';
import { useLeagueDashboard } from '@/hooks/sleeper/useLeagues';
import { DashboardSummary } from './DashboardSummary';
import { DashboardLeagues } from './DashboardLeagues';
import { TopAssets } from './TopAssets';

export const LeagueDashboardPage = () => {


  const dashboard = useLeagueDashboard();



  if (dashboard.fetching) {

    return (
      <div>
        <UsernameInput />
        <div className="dashboard-container">
          <p className="loading-text">
            Loading league dashboard...
          </p>
        </div>
      </div>
    );

  }



  if (!dashboard.data) {

    return (
      <div>
        <UsernameInput />
        <div className="dashboard-container">

          {
            dashboard.username
            ?
            <p className="no-results-text">
              No league dashboard found.
            </p>
            :
            <p className="no-results-text">
              Please connect Sleeper account.
            </p>
          }

        </div>
      </div>
    );

  }



  return (
    <div>
      <UsernameInput />

      <div className="dashboard-container">


        <DashboardSummary
          summary={
            dashboard.data.summary
          }
        />


        <DashboardLeagues
          leagues={
            dashboard.data.leagues
          }
        />


        <TopAssets
          assets={
            dashboard.data.top_assets
          }
        />


      </div>

    </div>

  );

};