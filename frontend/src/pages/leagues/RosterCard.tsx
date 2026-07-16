import { useState } from 'react';

import './RosterCard.css';

import { UserAvatar } from '@/components/users/UserAvatar';
import type {
  LeaguePick,
  LeagueRoster,
  LeagueRosterConstructionTarget,
} from '@/types';
import { PlayerTable } from './PlayerTable';
import { formatNumber } from '@/utils/format';
import { buildRosterConstructionRows } from './rosterConstruction';
import {
  getDraftPickColor,
  getPositionColor,
} from '@/utils/positions';


interface Props {
  roster: LeagueRoster;
  rosterConstructionTargets: LeagueRosterConstructionTarget[];
  draftPickProjectionSummary?: string | null;
}

function StatValue({
  value,
  rank,
}: {
  value: string | number;
  rank?: number;
}) {
  return (
    <>
      <strong>{value}</strong>
      <small>
        {
          rank
            ? `#${rank}`
            : '—'
        }
      </small>
    </>
  );
}

function PickList({
  picks,
  draftPickProjectionSummary,
}: {
  picks: LeaguePick[];
  draftPickProjectionSummary?: string | null;
}) {
  if (picks.length === 0) {
    return (
      <div className="league-empty-note">
        No draft picks resolved.
      </div>
    );
  }

  return (
    <div className="league-pick-list">
      {
        picks.some((pick) => pick.projected_slot !== null)
        && draftPickProjectionSummary
          ? (
            <div className="league-pick-summary">
              {draftPickProjectionSummary}
            </div>
          )
          : null
      }
      {
        picks.map((pick) => (
          <div
            key={`${pick.season}-${pick.round}-${pick.og_roster_id}`}
            className="league-pick-row"
            style={{
              borderLeftColor: getDraftPickColor(),
            }}
          >
            <div className="league-pick-copy">
              <strong>{pick.label}</strong>
            </div>

            <div className="league-pick-values">
              <span>KTC {formatNumber(pick.ktc_value)}</span>
              <span>FC {formatNumber(pick.fc_value)}</span>
              <span>Rookie WAR {formatNumber(pick.rookie_war_value)}</span>
            </div>
          </div>
        ))
      }
    </div>
  );
}
export function RosterCard({
  roster,
  rosterConstructionTargets,
  draftPickProjectionSummary,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const constructionRows = buildRosterConstructionRows(
    roster,
    rosterConstructionTargets,
  );

  return (
    <div className="roster-card">
      <header className="roster-header">
        <div className="roster-header-main">
          <p className="roster-header-kicker">Roster</p>
          <div className="player-with-avatar">
            <UserAvatar
              avatarId={roster.owner.avatar}
              name={roster.owner.display_name}
              size="sm"
            />

            <h3 className="roster-title">
              #{roster.rank} {roster.owner.display_name}
            </h3>
          </div>
          <p className="roster-subtitle">
            {roster.record} · PF {formatNumber(roster.actual_points_for)}
          </p>
        </div>

        <div className="roster-summary-hero">
          <span>Asset KTC</span>
          <StatValue
            value={formatNumber(roster.total_asset_ktc_value)}
            rank={roster.stat_ranks.total_asset_ktc_value}
          />
        </div>
      </header>

      <div className="roster-summary-grid">
        <div className="roster-summary-stat">
          <span>Proj pts</span>
          <StatValue
            value={formatNumber(roster.projected_points)}
            rank={roster.stat_ranks.projected_points}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Asset FC</span>
          <StatValue
            value={formatNumber(roster.total_asset_fc_value)}
            rank={roster.stat_ranks.total_asset_fc_value}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Player KTC</span>
          <StatValue
            value={formatNumber(roster.total_ktc_value)}
            rank={roster.stat_ranks.total_ktc_value}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Pick KTC</span>
          <StatValue
            value={formatNumber(roster.total_pick_ktc_value)}
            rank={roster.stat_ranks.total_pick_ktc_value}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Player FC</span>
          <StatValue
            value={formatNumber(roster.total_fc_value)}
            rank={roster.stat_ranks.total_fc_value}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Pick FC</span>
          <StatValue
            value={formatNumber(roster.total_pick_fc_value)}
            rank={roster.stat_ranks.total_pick_fc_value}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Pick WAR</span>
          <StatValue
            value={formatNumber(roster.total_pick_rookie_war_value)}
            rank={roster.stat_ranks.total_pick_rookie_war_value}
          />
        </div>
        <div className="roster-summary-stat">
          <span>R St WAR</span>
          <StatValue
            value={formatNumber(roster.total_redraft_starter_war)}
            rank={roster.stat_ranks.total_redraft_starter_war}
          />
        </div>
        <div className="roster-summary-stat">
          <span>R Ro WAR</span>
          <StatValue
            value={formatNumber(roster.total_redraft_roster_war)}
            rank={roster.stat_ranks.total_redraft_roster_war}
          />
        </div>
        <div className="roster-summary-stat">
          <span>D St WAR</span>
          <StatValue
            value={formatNumber(roster.total_dynasty_starter_war)}
            rank={roster.stat_ranks.total_dynasty_starter_war}
          />
        </div>
        <div className="roster-summary-stat">
          <span>D Ro WAR</span>
          <StatValue
            value={formatNumber(roster.total_dynasty_roster_war)}
            rank={roster.stat_ranks.total_dynasty_roster_war}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Avg age</span>
          <StatValue
            value={formatNumber(roster.average_age)}
            rank={roster.stat_ranks.average_age}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Open spots</span>
          <StatValue
            value={roster.open_roster_spots}
            rank={roster.stat_ranks.open_roster_spots}
          />
        </div>
        <div className="roster-summary-stat">
          <span>FAAB</span>
          <StatValue
            value={roster.faab_remaining}
            rank={roster.stat_ranks.faab_remaining}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Waiver</span>
          <StatValue
            value={roster.waiver_position}
            rank={roster.stat_ranks.waiver_position}
          />
        </div>
        <div className="roster-summary-stat">
          <span>Trades</span>
          <StatValue
            value={roster.total_trades}
            rank={roster.stat_ranks.total_trades}
          />
        </div>
      </div>

      <div className="roster-card-actions">
        <button
          className="button-secondary"
          type="button"
          onClick={() => {
            setExpanded(!expanded);
          }}
        >
          {
            expanded
              ? 'Hide roster detail'
              : 'Players & picks'
          }
        </button>
      </div>

      {
        expanded
          ? (
            <div className="roster-card-details">
              <section className="league-detail-section">
                <div className="league-detail-header">
                  <p>Roster construction</p>
                </div>

                <div className="roster-construction-grid">
                  {
                    constructionRows.map((row) => (
                      <article
                        key={row.position}
                        className="roster-construction-card"
                        style={{
                          borderTopColor: getPositionColor(row.position),
                        }}
                      >
                        <strong>{row.position}</strong>
                        <span>
                          {row.playerCount}
                          {' '}
                          spots now
                        </span>
                        <span>
                          {row.targetCount}
                          {' '}
                          league target
                        </span>
                        <span>
                          {row.warShare.toFixed(1)}
                          % historical WAR share
                        </span>
                        <small>
                          {
                            row.delta > 0
                              ? `${row.delta} over target`
                              : row.delta < 0
                                ? `${Math.abs(row.delta)} under target`
                                : 'On target'
                          }
                        </small>
                      </article>
                    ))
                  }
                </div>
              </section>

              <section className="league-detail-section">
                <div className="league-detail-header">
                  <p>Roster table</p>
                </div>

                <PlayerTable players={roster.players} />
              </section>

              <section className="league-detail-section">
                <div className="league-detail-header">
                  <p>Draft capital</p>
                </div>

                <PickList
                  picks={roster.picks}
                  draftPickProjectionSummary={draftPickProjectionSummary}
                />
              </section>
            </div>
          )
          : null
      }
    </div>
  );
}
