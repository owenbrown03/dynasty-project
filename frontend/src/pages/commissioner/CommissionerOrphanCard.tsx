import { useState } from 'react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type {
  CommissionerLineupSlot,
  CommissionerOrphanRoster,
  CommissionerPlayerAsset,
  ValueBasis,
} from '@/types';
import {
  formatSelectedValue as formatValue,
} from '@/utils/valueFormat';

function CommissionerPlayerRow({
  player,
  valueBasis,
}: {
  player: CommissionerPlayerAsset;
  valueBasis: ValueBasis;
}) {
  return (
    <div className="commissioner-player-row">
      <div className="player-with-avatar">
        <PlayerAvatar
          playerId={player.player_id}
          name={player.name}
          size="sm"
        />

        <div className="player-with-avatar-copy">
          <strong>{player.name}</strong>
          <span>
            {
              [player.position, player.team]
                .filter(Boolean)
                .join(' · ') || '—'
            }
          </span>
        </div>
      </div>

      <strong className="commissioner-player-value">
        {
          formatValue(
            player.selected_value,
            valueBasis,
          )
        }
      </strong>
    </div>
  );
}

function CommissionerLineupRow({
  slot,
  valueBasis,
}: {
  slot: CommissionerLineupSlot;
  valueBasis: ValueBasis;
}) {
  return (
    <div className="commissioner-player-row">
      <div className="commissioner-lineup-slot">
        <span className="commissioner-lineup-slot-label">
          {slot.slot}
        </span>

        {
          slot.player
            ? (
              <div className="player-with-avatar">
                <PlayerAvatar
                  playerId={slot.player.player_id}
                  name={slot.player.name}
                  size="sm"
                />

                <div className="player-with-avatar-copy">
                  <strong>{slot.player.name}</strong>
                  <span>
                    {
                      [
                        slot.player.position,
                        slot.player.team,
                      ]
                        .filter(Boolean)
                        .join(' · ') || '—'
                    }
                  </span>
                </div>
              </div>
            )
            : (
              <span className="commissioner-empty-slot">
                Empty
              </span>
            )
        }
      </div>

      <strong className="commissioner-player-value">
        {
          formatValue(
            slot.player?.selected_value ?? null,
            valueBasis,
          )
        }
      </strong>
    </div>
  );
}

export function CommissionerOrphanCard({
  orphan,
  valueBasis,
}: {
  orphan: CommissionerOrphanRoster;
  valueBasis: ValueBasis;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="commissioner-card">
      <header className="commissioner-card-header">
        <div className="commissioner-card-heading">
          <p className="commissioner-card-kicker">
            League
          </p>
          <h2 className="commissioner-card-title">
            {orphan.league_name}
          </h2>
          <p className="commissioner-card-subtitle">
            {orphan.roster_name}
          </p>
        </div>

        <div className="commissioner-card-stats">
          <div>
            <span>Roster value</span>
            <strong>
              {
                formatValue(
                  orphan.roster_value,
                  valueBasis,
                )
              }
            </strong>
          </div>

          <div>
            <span>League avg</span>
            <strong>
              {
                formatValue(
                  orphan.league_average_value,
                  valueBasis,
                )
              }
            </strong>
          </div>

          <div>
            <span>Avg age</span>
            <strong>
              {
                orphan.average_age !== null
                  ? orphan.average_age.toFixed(1)
                  : '—'
              }
            </strong>
          </div>
        </div>
      </header>

      <div className="commissioner-badge-row">
        {
          orphan.settings_badges.map((badge) => (
            <span
              key={`${orphan.league_id}-${orphan.roster_id}-${badge}`}
              className="commissioner-badge"
            >
              {badge}
            </span>
          ))
        }
      </div>

      <section className="commissioner-section">
        <div className="commissioner-section-header">
          <p>Mocked starting lineup</p>
        </div>

        <div className="commissioner-list">
          {
            orphan.lineup.map((slot) => (
              <CommissionerLineupRow
                key={`${orphan.league_id}-${orphan.roster_id}-${slot.slot}`}
                slot={slot}
                valueBasis={valueBasis}
              />
            ))
          }
        </div>
      </section>

      <div className="commissioner-card-actions">
        <button
          className="button-secondary"
          type="button"
          onClick={() => {
            setExpanded(!expanded);
          }}
        >
          {
            expanded
              ? 'Hide details'
              : 'Bench & picks'
          }
        </button>
      </div>

      {
        expanded
          ? (
            <div className="commissioner-card-details">
              <section className="commissioner-section">
                <div className="commissioner-section-header">
                  <p>Bench assets</p>
                </div>

                <div className="commissioner-list">
                  {
                    orphan.bench.length > 0
                      ? orphan.bench.map((player) => (
                          <CommissionerPlayerRow
                            key={player.player_id}
                            player={player}
                            valueBasis={valueBasis}
                          />
                        ))
                      : (
                        <div className="commissioner-empty-note">
                          No bench assets.
                        </div>
                      )
                  }
                </div>
              </section>

              <section className="commissioner-section">
                <div className="commissioner-section-header">
                  <p>Draft capital</p>
                </div>

                <div className="commissioner-list">
                  {
                    orphan.picks.length > 0
                      ? orphan.picks.map((pick) => (
                          <div
                            key={`${pick.season}-${pick.round}-${pick.og_roster_id}`}
                            className="commissioner-pick-row"
                          >
                            <div className="commissioner-pick-copy">
                              <span className="commissioner-pick-label">
                                {pick.label}
                              </span>

                              {
                                pick.slot_source_label
                                  ? (
                                    <span className="commissioner-pick-meta">
                                      {pick.slot_source_label}
                                    </span>
                                  )
                                  : null
                              }

                              {
                                pick.value_source_label
                                  ? (
                                    <span className="commissioner-pick-meta">
                                      {pick.value_source_label}
                                    </span>
                                  )
                                  : null
                              }
                            </div>

                            <strong className="commissioner-player-value">
                              {
                                formatValue(
                                  pick.selected_value,
                                  valueBasis,
                                )
                              }
                            </strong>
                          </div>
                        ))
                      : (
                        <div className="commissioner-empty-note">
                          No draft picks resolved.
                        </div>
                      )
                  }
                </div>
              </section>
            </div>
          )
          : null
      }
    </article>
  );
}
