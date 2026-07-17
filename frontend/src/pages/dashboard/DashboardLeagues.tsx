import { LeagueAvatar } from '@/components/leagues/LeagueAvatar';
import { useValuePreference } from '@/context/useValuePreference';
import { useBootstrapContext } from '@/context/useBootstrapContext';
import type { DashboardLeague } from '@/types';
import { useNavigate } from 'react-router';
import {
  getDashboardLeagueSelectedRank,
  getDashboardLeagueSelectedValue,
  getValueBasisLabel,
} from '@/utils/valueBasis';

interface Props {
  leagues: DashboardLeague[];
}

function formatLeagueRecord(
  league: DashboardLeague,
) {
  if (league.ties > 0) {
    return `${league.wins}-${league.losses}-${league.ties}`;
  }

  return `${league.wins}-${league.losses}`;
}

function formatOrdinal(
  value: number | null | undefined,
) {
  if (!value) {
    return '—';
  }

  const mod10 = value % 10;
  const mod100 = value % 100;

  if (mod10 === 1 && mod100 !== 11) {
    return `${value}st`;
  }

  if (mod10 === 2 && mod100 !== 12) {
    return `${value}nd`;
  }

  if (mod10 === 3 && mod100 !== 13) {
    return `${value}rd`;
  }

  return `${value}th`;
}

function formatCurrency(
  value: number | null | undefined,
) {
  if (value == null) {
    return '—';
  }

  return value.toLocaleString(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  });
}

export function DashboardLeagues({
  leagues,
}: Props) {
  const navigate = useNavigate();
  const valuePreference = useValuePreference();
  const { bootstrap } = useBootstrapContext();
  const selectedLabel = getValueBasisLabel(
    valuePreference.preference,
  );

  return (
    <section className="dashboard-section">
      <div className="dashboard-section-header">
        <div>
          <p className="dashboard-section-kicker">
            Leagues
          </p>
        </div>
      </div>

      <div className="portfolio-league-table">
        <div className="portfolio-league-table-head">
          <span>League</span>
          <span>Standing</span>
          <span>Projected $</span>
          <span>Construction</span>
          <span>{selectedLabel}</span>
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
              <LeagueAvatar
                avatarId={league.avatar}
                name={league.league_name}
                size="md"
              />

              <div>
                <h3 className="portfolio-league-title">
                  {league.league_name}
                </h3>

                <p className="portfolio-league-subtitle">
                  {formatLeagueRecord(league)} · PF #{league.points_for_rank}
                </p>
              </div>
            </div>

            <div className="portfolio-league-metrics">
              <div className="portfolio-league-metric">
                <span>Standing</span>
                <strong>
                  {formatOrdinal(league.standings_rank)}
                </strong>
                <small>
                  of {league.league_size}
                </small>
              </div>

              <div className="portfolio-league-metric">
                <span>Projected payout</span>
                <strong>
                  {formatCurrency(league.projected_payout)}
                </strong>
                <small>
                  {league.projected_seed
                    ? `Seed ${formatOrdinal(league.projected_seed)}`
                    : 'No seed yet'}
                </small>
              </div>

              <div className="portfolio-league-metric">
                <span>Construction</span>
                <strong>
                  {league.roster_construction_alignment_pct != null
                    ? `${league.roster_construction_alignment_pct.toFixed(0)}%`
                    : '—'}
                </strong>
                <small>
                  {league.roster_construction_moves_needed != null
                    ? `${league.roster_construction_moves_needed} move${
                      league.roster_construction_moves_needed === 1
                        ? ''
                        : 's'
                    } off`
                    : 'Unavailable'}
                </small>
              </div>

              <div className="portfolio-league-metric">
                <span>{selectedLabel}</span>
                <strong>
                  {
                    getDashboardLeagueSelectedValue(
                      league,
                      valuePreference.preference,
                      bootstrap?.war_value_settings,
                    )?.toLocaleString(undefined, {
                      maximumFractionDigits: (
                        valuePreference.preference === 'ktc'
                        || valuePreference.preference === 'fantasycalc'
                          ? 0
                          : 2
                      ),
                      minimumFractionDigits: (
                        valuePreference.preference === 'ktc'
                        || valuePreference.preference === 'fantasycalc'
                          ? 0
                          : 2
                      ),
                    }) ?? '—'
                  }
                </strong>
                <small>
                  {
                    getDashboardLeagueSelectedRank(
                      league,
                      valuePreference.preference,
                    )
                      ? `#${getDashboardLeagueSelectedRank(
                        league,
                        valuePreference.preference,
                        bootstrap?.war_value_settings,
                      )}`
                      : '—'
                  }
                </small>
              </div>

              <div className="portfolio-league-metric">
                <span>Average age</span>
                <strong>
                  {league.average_age
                    ? league.average_age.toFixed(1)
                    : 'N/A'}
                </strong>
                <small>#{league.age_rank} youngest</small>
              </div>
            </div>
          </button>
        ))}
        </div>
      </div>
    </section>
  );
}
