import { useState } from 'react';

import './RosterCard.css';

import { UserAvatar } from '@/components/users/UserAvatar';
import type {
  LeaguePick,
  LeagueRoster,
  LeagueRosterConstructionTarget,
  ValueBasis,
  WarValueSettings,
} from '@/types';
import { PlayerTable } from './PlayerTable';
import { formatNumber } from '@/utils/format';
import { buildRosterConstructionRows } from './rosterConstruction';
import {
  getDraftPickColor,
  getPositionColor,
} from '@/utils/positions';
import {
  getPickSelectedValue,
  getPickValueLabel,
  getRosterSelectedAssetRank,
  getRosterSelectedAssetValue,
  getRosterSelectedPickRank,
  getRosterSelectedPickValue,
  getRosterSelectedPlayerRank,
  getRosterSelectedPlayerValue,
  getValueBasisLabel,
} from '@/utils/valueBasis';


interface Props {
  roster: LeagueRoster;
  displayRank: number;
  rosterConstructionTargets: LeagueRosterConstructionTarget[];
  draftPickProjectionSummary?: string | null;
  valueBasis: ValueBasis;
  warValueSettings: WarValueSettings;
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
  valueBasis,
}: {
  picks: LeaguePick[];
  draftPickProjectionSummary?: string | null;
  valueBasis: ValueBasis;
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
              <span>
                {getPickValueLabel(valueBasis)}
                {' '}
                {
                  formatNumber(
                    getPickSelectedValue(
                      pick,
                      valueBasis,
                    ),
                    (
                      valueBasis === 'ktc'
                      || valueBasis === 'fantasycalc'
                    )
                      ? 0
                      : 2,
                  )
                }
              </span>
            </div>
          </div>
        ))
      }
    </div>
  );
}
export function RosterCard({
  roster,
  displayRank,
  rosterConstructionTargets,
  draftPickProjectionSummary,
  valueBasis,
  warValueSettings,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const constructionRows = buildRosterConstructionRows(
    roster,
    rosterConstructionTargets,
  );
  const selectedValueLabel = getValueBasisLabel(
    valueBasis,
  );
  const selectedAssetValue = getRosterSelectedAssetValue(
    roster,
    valueBasis,
    warValueSettings,
  );
  const selectedPlayerValue = getRosterSelectedPlayerValue(
    roster,
    valueBasis,
    warValueSettings,
  );
  const selectedPickValue = getRosterSelectedPickValue(
    roster,
    valueBasis,
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
              #{displayRank} {roster.owner.display_name}
            </h3>
          </div>
          <p className="roster-subtitle">
            {roster.record} · PF {formatNumber(roster.actual_points_for)}
          </p>
        </div>

        <div className="roster-summary-hero">
          <span>{selectedValueLabel}</span>
          <StatValue
            value={
              formatNumber(
                selectedAssetValue,
                (
                  valueBasis === 'ktc'
                  || valueBasis === 'fantasycalc'
                )
                  ? 0
                  : 2,
              )
            }
            rank={getRosterSelectedAssetRank(
              roster,
              valueBasis,
              warValueSettings,
            )}
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
          <span>{selectedValueLabel} players</span>
          <StatValue
            value={
              formatNumber(
                selectedPlayerValue,
                (
                  valueBasis === 'ktc'
                  || valueBasis === 'fantasycalc'
                )
                  ? 0
                  : 2,
              )
            }
            rank={getRosterSelectedPlayerRank(
              roster,
              valueBasis,
              warValueSettings,
            )}
          />
        </div>
        <div className="roster-summary-stat">
          <span>{getPickValueLabel(valueBasis)}</span>
          <StatValue
            value={
              formatNumber(
                selectedPickValue,
                (
                  valueBasis === 'ktc'
                  || valueBasis === 'fantasycalc'
                )
                  ? 0
                  : 2,
              )
            }
            rank={getRosterSelectedPickRank(
              roster,
              valueBasis,
            )}
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
          <span>Waiver moves</span>
          <StatValue
            value={roster.total_moves}
            rank={roster.stat_ranks.total_moves}
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

                <PlayerTable
                  players={roster.players}
                  valueBasis={valueBasis}
                  warValueSettings={warValueSettings}
                />
              </section>

              <section className="league-detail-section">
                <div className="league-detail-header">
                  <p>Draft capital</p>
                </div>

                <PickList
                  picks={roster.picks}
                  draftPickProjectionSummary={draftPickProjectionSummary}
                  valueBasis={valueBasis}
                />
              </section>
            </div>
          )
          : null
      }
    </div>
  );
}
