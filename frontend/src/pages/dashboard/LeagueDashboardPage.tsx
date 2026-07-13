import './LeagueDashboardPage.css';

import { LoadingState } from '@/components/feedback/LoadingState';
import { UserAvatar } from '@/components/users/UserAvatar';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { UsernameInput } from './UsernameInput';
import { useLeagueDashboard } from '@/hooks/sleeper/useLeagues';
import { DashboardSummary } from './DashboardSummary';
import { DashboardLeagues } from './DashboardLeagues';
import { TopAssets } from './TopAssets';

export const LeagueDashboardPage = () => {
  const dashboard = useLeagueDashboard();
  const connection = useSleeperConnection();

  if (dashboard.fetching) {
    return (
      <div className="dashboard-page">
        <UsernameInput />

        <div className="dashboard-container">
          <LoadingState label="Loading league dashboard..." />
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
              <UserAvatar
                avatarId={connection.avatar}
                name={dashboard.username}
                size="lg"
                className="dashboard-profile-avatar"
              />

              <div className="dashboard-hero-meta-copy">
                <span className="dashboard-meta-label">
                  Sleeper profile
                </span>

                <strong className="dashboard-meta-value">
                  {dashboard.username}
                </strong>
              </div>
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
