import type { DashboardLeague } from '@/types';
import { useNavigate } from 'react-router';
interface Props {
  leagues: DashboardLeague[];
}

export function DashboardLeagues({
  leagues,
}: Props) {
  const navigate = useNavigate();

  return (
    <section className="dashboard-section">
      <div className="dashboard-section-header">
        <div>
          <p className="dashboard-section-kicker">
            Leagues
          </p>

          <h2 className="dashboard-section-title">
            Cross-league rankings
          </h2>
        </div>
      </div>

      <div className="portfolio-league-table">
        <div className="portfolio-league-table-head">
          <span>League</span>
          <span>KTC</span>
          <span>FC</span>
          <span>Dynasty S</span>
          <span>Dynasty R</span>
          <span>Redraft S</span>
          <span>Redraft R</span>
          <span>Age</span>
        </div>

        <div className="portfolio-league-list">
        {leagues.map((league) => (
          <button
            key={league.league_id}
            type="button"
            className="portfolio-league-row"
            onClick={() =>
              navigate('/leagues', {
                state: {
                  leagueId: league.league_id,
                },
              })
            }
          >
            <div className="portfolio-league-primary">
              <div>
                <h3 className="portfolio-league-title">
                  {league.league_name}
                </h3>

                <p className="portfolio-league-subtitle">
                  {league.league_size}
                  {' '}teams
                </p>
              </div>
            </div>

            <div className="portfolio-league-metrics">
              <div className="portfolio-league-metric">
                <span>KTC</span>
                <strong>{league.ktc_value.toLocaleString()}</strong>
                <small>#{league.ktc_rank}</small>
              </div>

              <div className="portfolio-league-metric">
                <span>FC</span>
                <strong>{league.fc_value.toLocaleString()}</strong>
                <small>#{league.fc_rank}</small>
              </div>

              <div className="portfolio-league-metric">
                <span>Dynasty starter</span>
                <strong>{league.dynasty_starter_war.toFixed(2)}</strong>
                <small>#{league.dynasty_starter_war_rank}</small>
              </div>

              <div className="portfolio-league-metric">
                <span>Dynasty roster</span>
                <strong>{league.dynasty_roster_war.toFixed(2)}</strong>
                <small>#{league.dynasty_roster_war_rank}</small>
              </div>

              <div className="portfolio-league-metric">
                <span>Redraft starter</span>
                <strong>{league.redraft_starter_war.toFixed(2)}</strong>
                <small>#{league.redraft_starter_war_rank}</small>
              </div>

              <div className="portfolio-league-metric">
                <span>Redraft roster</span>
                <strong>{league.redraft_roster_war.toFixed(2)}</strong>
                <small>#{league.redraft_roster_war_rank}</small>
              </div>

              <div className="portfolio-league-metric">
                <span>Average age</span>
                <strong>
                  {league.average_age
                    ? league.average_age.toFixed(1)
                    : 'N/A'}
                </strong>
                <small>#{league.age_rank}</small>
              </div>
            </div>
          </button>
        ))}
        </div>
      </div>
    </section>
  );
}
