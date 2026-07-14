import './LeagueDashboardPage.css';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useLeagueDashboard } from '@/hooks/sleeper/useLeagues';
import { DashboardSummary } from './DashboardSummary';
import { DashboardLeagues } from './DashboardLeagues';
import { TopAssets } from './TopAssets';

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
            Enter your Sleeper username to view your
            leagues, assets, and WAR profile.
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

  if (dashboard.fetching) {
    return (
      <div className="dashboard-page">
        <section className="page-header dashboard-hero">
          <div className="dashboard-hero-text">
            <p className="page-eyebrow">Portfolio dashboard</p>
            <h1 className="page-title">Cross-league roster view</h1>
            <p className="page-description">
              Review your leagues, asset base,
              and WAR profile from one screen.
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
          <LoadingState label="Loading league dashboard..." />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <section className="page-header dashboard-hero">
        <div className="dashboard-hero-text">
          <p className="page-eyebrow">Portfolio dashboard</p>
          <h1 className="page-title">Cross-league roster view</h1>
          <p className="page-description">
            Review your leagues, asset base,
            and WAR profile from one screen.
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
        {dashboard.data ? (
          <>
            <DashboardSummary summary={dashboard.data.summary} />
            <DashboardLeagues leagues={dashboard.data.leagues} />
            <TopAssets assets={dashboard.data.top_assets} />
          </>
        ) : (
          <p className="no-results-text">
            No league dashboard found.
          </p>
        )}
      </div>
    </div>
  );
};
