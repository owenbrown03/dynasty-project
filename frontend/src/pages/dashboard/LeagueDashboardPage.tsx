import './LeagueDashboardPage.css';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';

import { Skeleton } from '@/components/feedback/Skeleton';
import { LoadingState } from '@/components/feedback/LoadingState';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useLeagueDashboard } from '@/hooks/sleeper/useLeagues';
import { DashboardLeagues } from './DashboardLeagues';

function DashboardSkeleton() {
  return (
    <div className="dashboard-skeleton" role="status" aria-live="polite">
      <span className="skeleton-sr-label">Loading league dashboard...</span>

      <section className="dashboard-section">
        <div className="dashboard-section-header">
          <div>
            <Skeleton width={120} variant="text" />
            <Skeleton width={220} variant="title" />
          </div>
        </div>

        <div className="summary-grid">
          {
            Array.from({ length: 3 }).map((_, index) => (
              <div className="summary-card skeleton-card" key={index}>
                <Skeleton width={100} variant="text" />
                <Skeleton width={72} height={26} />
              </div>
            ))
          }
        </div>
      </section>

      <div className="portfolio-league-table">
        <div className="portfolio-league-table-head">
          {
            ['League', 'Record', 'Standing', 'Roster', 'Value', 'Projection'].map((label) => (
              <span key={label}>{label}</span>
            ))
          }
        </div>

        <div className="portfolio-league-list">
          {
            Array.from({ length: 8 }).map((_, index) => (
              <div className="portfolio-league-row portfolio-league-row-skeleton" key={index}>
                <div className="portfolio-league-primary">
                  <Skeleton variant="circle" width={38} height={38} />
                  <div>
                    <Skeleton width={170} variant="title" />
                    <Skeleton width={110} variant="text" />
                  </div>
                </div>

                <div className="portfolio-league-metrics">
                  {
                    Array.from({ length: 5 }).map((__, metricIndex) => (
                      <div className="portfolio-league-metric" key={metricIndex}>
                        <Skeleton width="70%" height={18} />
                      </div>
                    ))
                  }
                </div>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  );
}

export const LeagueDashboardPage = () => {
  const dashboard = useLeagueDashboard();
  const connection = useSleeperConnection();
  const [input, setInput] = useState('');

  useEffect(() => {
    setInput(connection.username ?? '');
  }, [connection.username]);

  const submit = async () => {
    const nextUsername = input.trim();
    if (!nextUsername) return;

    await toast.promise(
      connection.upsertConnection(nextUsername),
      {
        loading: 'Syncing profile...',
        success: 'Profile synced!',
        error: 'Failed to sync username',
      }
    );
  };

  if (!connection.username) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-onboarding">
          <h1 className="page-title">Portfolio dashboard</h1>
          <p className="page-description">
            Enter your Sleeper username to view your leagues.
          </p>

          <div className="dashboard-hero-input">
            <input
              className="username-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
              placeholder="Sleeper username"
            />
            <button className="button-secondary" onClick={submit}>
              Get started
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (dashboard.loading) {
    return (
      <div className="dashboard-page">
        <section className="page-header dashboard-hero">
          <div className="dashboard-hero-text">
            <p className="page-eyebrow">Portfolio dashboard</p>
            <h1 className="page-title">{connection.username}'s leagues</h1>
            <p className="page-description">
              Review your leagues from one screen.
            </p>
          </div>

          <div className="dashboard-hero-input">
            <input
              className="username-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
              placeholder="Sleeper username"
            />
            <button className="button-secondary" onClick={submit}>
              Sync
            </button>
          </div>
        </section>

        <div className="dashboard-container">
          <DashboardSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <section className="page-header dashboard-hero">
        <div className="dashboard-hero-text">
          <p className="page-eyebrow">Portfolio dashboard</p>
          <h1 className="page-title">{connection.username}'s leagues</h1>
          <p className="page-description">
            Review your leagues from one screen.
          </p>
          {dashboard.fetching && !dashboard.loading && (
            <LoadingState label="Updating dashboard data..." inline className="dashboard-refresh-indicator" />
          )}
        </div>

        <div className="dashboard-hero-input">
          <input
            className="username-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            placeholder="Sleeper username"
          />
          <button className="button-secondary" onClick={submit}>
            Sync
          </button>
        </div>
      </section>

      <div className="dashboard-container">
        {dashboard.data ? (
          <DashboardLeagues leagues={dashboard.data.leagues} />
        ) : (
          <p className="no-results-text">
            No league dashboard found.
          </p>
        )}
      </div>
    </div>
  );
};
