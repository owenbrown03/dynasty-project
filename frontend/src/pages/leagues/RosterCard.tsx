import { useState } from 'react';

import './RosterCard.css';

import { UserAvatar } from '@/components/users/UserAvatar';
import type { LeaguePick, LeagueRoster } from '@/types';
import { PlayerTable } from './PlayerTable';
import { formatNumber } from '@/utils/format';


interface Props {
  roster: LeagueRoster;
}


function PickList({
  picks,
}: {
  picks: LeaguePick[];
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
        picks.map((pick) => (
          <div
            key={`${pick.season}-${pick.round}-${pick.og_roster_id}`}
            className="league-pick-row"
          >
            <div className="league-pick-copy">
              <strong>{pick.label}</strong>
              {
                pick.slot_source_label
                  ? (
                    <span className="league-pick-meta">
                      {pick.slot_source_label}
                    </span>
                  )
                  : null
              }
            </div>

            <div className="league-pick-values">
              <span>KTC {formatNumber(pick.ktc_value)}</span>
              <span>FC {formatNumber(pick.fc_value)}</span>
            </div>
          </div>
        ))
      }
    </div>
  );
}


export function RosterCard({ roster }: Props) {
  const [expanded, setExpanded] = useState(false);

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
          <strong>{formatNumber(roster.total_asset_ktc_value)}</strong>
        </div>
      </header>

      <div className="roster-summary-grid">
        <div className="roster-summary-stat">
          <span>Proj pts</span>
          <strong>{formatNumber(roster.projected_points)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Asset FC</span>
          <strong>{formatNumber(roster.total_asset_fc_value)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Player KTC</span>
          <strong>{formatNumber(roster.total_ktc_value)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Pick KTC</span>
          <strong>{formatNumber(roster.total_pick_ktc_value)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Player FC</span>
          <strong>{formatNumber(roster.total_fc_value)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Pick FC</span>
          <strong>{formatNumber(roster.total_pick_fc_value)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>R St WAR</span>
          <strong>{formatNumber(roster.total_redraft_starter_war)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>R Ro WAR</span>
          <strong>{formatNumber(roster.total_redraft_roster_war)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>D St WAR</span>
          <strong>{formatNumber(roster.total_dynasty_starter_war)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>D Ro WAR</span>
          <strong>{formatNumber(roster.total_dynasty_roster_war)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Avg age</span>
          <strong>{formatNumber(roster.average_age)}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Open spots</span>
          <strong>{roster.open_roster_spots}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>FAAB</span>
          <strong>{roster.faab_remaining}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Waiver</span>
          <strong>{roster.waiver_position}</strong>
        </div>
        <div className="roster-summary-stat">
          <span>Moves</span>
          <strong>{roster.total_moves}</strong>
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
                  <p>Draft capital</p>
                </div>

                <PickList picks={roster.picks} />
              </section>

              <section className="league-detail-section">
                <div className="league-detail-header">
                  <p>Roster table</p>
                </div>

                <PlayerTable players={roster.players} />
              </section>
            </div>
          )
          : null
      }
    </div>
  );
}
