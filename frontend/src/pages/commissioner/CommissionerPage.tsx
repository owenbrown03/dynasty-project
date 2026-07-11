import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router';

import { LoadingState } from '@/components/feedback/LoadingState';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { useValuePreference } from '@/context/useValuePreference';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useCommissionerOrphans } from '@/hooks/sleeper/useUsers';
import type {
  CommissionerLineupSlot,
  CommissionerOrphanRoster,
  CommissionerPlayerAsset,
  ValueBasis,
} from '@/types';
import { VALUE_BASIS_OPTIONS } from '@/pages/waivers/waiver.constants';

import './CommissionerPage.css';


type CommissionerTab = 'orphans';

const DEFAULT_TAB: CommissionerTab = 'orphans';


function isValueBasis(
  value: string | null,
): value is ValueBasis {
  return VALUE_BASIS_OPTIONS.some(
    (option) => option.value === value,
  );
}


function formatValue(
  value: number | null,
  valueBasis: ValueBasis,
) {
  if (value === null) {
    return '—';
  }

  if (
    valueBasis === 'ktc'
    || valueBasis === 'fantasycalc'
  ) {
    return Math.round(value).toLocaleString();
  }

  return value.toFixed(2);
}


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


function CommissionerOrphanCard({
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
        <div>
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


export const CommissionerPage = () => {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const valuePreference = useValuePreference();
  const connection = useSleeperConnection();

  const routeUsername = params.username ?? null;
  const activeUsername = routeUsername ?? connection.username ?? null;
  const [usernameInput, setUsernameInput] = useState(
    activeUsername ?? '',
  );

  useEffect(() => {
    setUsernameInput(activeUsername ?? '');
  }, [activeUsername]);

  const activeTab = (
    searchParams.get('tab') === 'orphans'
      ? 'orphans'
      : DEFAULT_TAB
  ) as CommissionerTab;

  const valueBasis = isValueBasis(
    searchParams.get('basis'),
  )
    ? (searchParams.get('basis') as ValueBasis)
    : valuePreference.preference;

  const orphans = useCommissionerOrphans(
    activeUsername,
    valueBasis,
  );

  const shareUrl = useMemo(() => {
    if (!activeUsername) {
      return '';
    }

    return `${window.location.origin}/commissioner/${encodeURIComponent(activeUsername)}?tab=${activeTab}&basis=${valueBasis}`;
  }, [
    activeTab,
    activeUsername,
    valueBasis,
  ]);

  const setTab = (tab: CommissionerTab) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', tab);
    next.set('basis', valueBasis);
    setSearchParams(next);
  };

  const setBasis = (nextBasis: ValueBasis) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', activeTab);
    next.set('basis', nextBasis);
    setSearchParams(next);
  };

  const handleOpen = () => {
    const trimmed = usernameInput.trim();

    if (!trimmed) {
      return;
    }

    navigate(
      `/commissioner/${encodeURIComponent(trimmed)}?tab=${activeTab}&basis=${valueBasis}`,
    );
  };

  return (
    <main className="commissioner-page">
      <section className="commissioner-page-header">
        <div>
          <p className="page-eyebrow">Commissioner</p>
          <h1 className="commissioner-page-title">
            Commissioner board
          </h1>
          <p className="commissioner-page-description">
            Review public orphan rosters, league settings, starting lineup
            strength, and draft capital from a shareable Sleeper username URL.
          </p>
        </div>

        <div className="commissioner-toolbar">
          <label className="commissioner-username-control">
            <span>Sleeper username</span>

            <div className="commissioner-username-row">
              <input
                value={usernameInput}
                onChange={(event) => {
                  setUsernameInput(event.target.value);
                }}
                placeholder="Enter Sleeper username"
              />

              <button
                className="button-primary"
                type="button"
                onClick={handleOpen}
              >
                Open
              </button>
            </div>
          </label>

          <label className="waivers-value-selector">
            <span>Value Basis</span>

            <select
              value={valueBasis}
              onChange={(event) => {
                setBasis(
                  event.target.value as ValueBasis,
                );
              }}
            >
              {
                VALUE_BASIS_OPTIONS.map((option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ))
              }
            </select>
          </label>

          {
            shareUrl
              ? (
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => {
                    void navigator.clipboard.writeText(
                      shareUrl,
                    );
                  }}
                >
                  Copy link
                </button>
              )
              : null
          }
        </div>
      </section>

      <div className="commissioner-tabs" role="tablist" aria-label="Commissioner tabs">
        <button
          className={
            activeTab === 'orphans'
              ? 'commissioner-tab-button active'
              : 'commissioner-tab-button'
          }
          type="button"
          onClick={() => {
            setTab('orphans');
          }}
        >
          Available Orphans
        </button>
      </div>

      {
        !activeUsername
          ? (
            <div className="commissioner-empty-state">
              Enter a Sleeper username or link an account to open a shareable commissioner view.
            </div>
          )
          : null
      }

      {
        activeUsername && orphans.loading
          ? (
            <LoadingState
              label="Loading commissioner view..."
              className="commissioner-empty-state"
            />
          )
          : null
      }

      {
        activeUsername && !orphans.loading && orphans.error
          ? (
            <div className="commissioner-empty-state">
              Unable to load commissioner data for "{activeUsername}".
            </div>
          )
          : null
      }

      {
        activeUsername && !orphans.loading && orphans.data && orphans.data.orphans.length === 0
          ? (
            <div className="commissioner-empty-state">
              No orphan rosters found for "{activeUsername}".
            </div>
          )
          : null
      }

      {
        activeUsername && orphans.data && orphans.data.orphans.length > 0
          ? (
            <section className="commissioner-card-grid">
              {
                orphans.data.orphans.map((orphan) => (
                  <CommissionerOrphanCard
                    key={`${orphan.league_id}-${orphan.roster_id}`}
                    orphan={orphan}
                    valueBasis={valueBasis}
                  />
                ))
              }
            </section>
          )
          : null
      }
    </main>
  );
};
