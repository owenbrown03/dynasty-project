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
      <div className="dashboard-page">
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
      <div className="dashboard-page">
        <UsernameInput />

        <div className="dashboard-container">
          {dashboard.username ? (
            <p className="no-results-text">
              No league dashboard found.
            </p>
          ) : (
            <p className="no-results-text">
              Please connect Sleeper account.
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <UsernameInput />

      <div className="dashboard-container">
        <section className="dashboard-hero">
          <div>
            <p className="page-eyebrow">
              Portfolio dashboard
            </p>

            <h1 className="dashboard-title">
              Cross-league roster view
            </h1>

            <p className="dashboard-description">
              Review your leagues, asset base,
              and WAR profile from one screen.
            </p>
          </div>

          {dashboard.username && (
            <div className="dashboard-hero-meta">
              <span className="dashboard-meta-label">
                Sleeper profile
              </span>

              <strong className="dashboard-meta-value">
                {dashboard.username}
              </strong>
            </div>
          )}
        </section>

        <DashboardSummary
          summary={dashboard.data.summary}
        />

        <DashboardLeagues
          leagues={dashboard.data.leagues}
        />

        <TopAssets
          assets={dashboard.data.top_assets}
        />
      </div>
    </div>
  );
};
