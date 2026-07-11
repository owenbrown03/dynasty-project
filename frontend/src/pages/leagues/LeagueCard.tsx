import './LeagueCard.css';

import type { LeagueDetails } from '@/types';
import { RosterCard } from './RosterCard';


interface Props {
  league: LeagueDetails;
}


export function LeagueCard({
  league,
}: Props) {
  return (
    <div className="league-card">
      <header className="league-header">
        <div>
          <p className="league-header-kicker">League</p>
          <h2 className="league-title">{league.league_name}</h2>
          <p className="league-subtitle">
            {league.season} · {league.total_rosters} teams
          </p>
        </div>

        <div className="league-summary-stat">
          <strong>{league.rosters.length}</strong>
          <small>rosters</small>
        </div>
      </header>

      <div className="league-badge-row">
        {
          league.settings_badges.map((badge) => (
            <span
              key={`${league.league_id}-${badge}`}
              className="league-badge"
            >
              {badge}
            </span>
          ))
        }
      </div>

      <section className="league-settings-panel">
        <div className="league-settings-header">
          <p>League settings</p>
        </div>

        <div className="league-settings-grid">
          {
            league.settings_details.map((detail) => (
              <div
                key={`${league.league_id}-${detail.label}`}
                className="league-settings-item"
              >
                <span>{detail.label}</span>
                <strong>{detail.value}</strong>
              </div>
            ))
          }
        </div>
      </section>

      <div className="rosters">
        {league.rosters.map((roster) => (
          <RosterCard
            key={roster.roster_id}
            roster={roster}
          />
        ))}
      </div>
    </div>
  );
}
