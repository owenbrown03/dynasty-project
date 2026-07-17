import { useMemo, useState } from 'react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { useValuePreference } from '@/context/useValuePreference';
import { useLeagueOverview } from '@/hooks/sleeper/useLeagues';
import { usePlayerTiers } from '@/hooks/sleeper/usePlayerTiers';
import type {
  TierBoardPlayer,
  TierBoardSource,
  ValueBasis,
} from '@/types';
import { getPositionColor } from '@/utils/positions';

import {
  TIER_SOURCE_OPTIONS,
  WAR_ONLY_OPTIONS,
} from './tier.constants';
import './TiersPage.css';


function formatSelectedValue(
  player: TierBoardPlayer,
  valueBasis: ValueBasis,
) {
  if (
    valueBasis === 'ktc'
    || valueBasis === 'fantasycalc'
    || valueBasis === 'adp'
  ) {
    return Math.round(
      player.selected_value,
    ).toLocaleString();
  }

  return player.selected_value.toFixed(2);
}

function formatExposure(
  player: TierBoardPlayer,
) {
  if (
    player.exposure_pct == null
    || player.exposure_owned_leagues == null
    || player.exposure_total_leagues == null
  ) {
    return null;
  }

  return `${player.exposure_pct.toFixed(1)}% · ${player.exposure_owned_leagues}/${player.exposure_total_leagues}`;
}

function getExposureTone(
  player: TierBoardPlayer,
) {
  const exposurePct = player.exposure_pct;

  if (exposurePct == null) {
    return null;
  }

  if (exposurePct === 0 || exposurePct >= 25) {
    return 'danger';
  }

  if (exposurePct >= 6 && exposurePct <= 10) {
    return 'success';
  }

  return 'warning';
}


export const TiersPage = () => {
  const valuePreference = useValuePreference();
  const initialSource = valuePreference.preference;
  const initialWarBasis: ValueBasis = (
    initialSource === 'my_war'
    || initialSource === 'sleeper_war'
  )
    ? initialSource
    : 'sleeper_war';
  const [source, setSource] = useState<TierBoardSource>(
    initialSource === 'my_war'
      || initialSource === 'sleeper_war'
      ? 'league_war'
      : initialSource,
  );
  const [warBasis, setWarBasis] = useState<ValueBasis>(
    initialWarBasis,
  );
  const [leagueId, setLeagueId] = useState('');

  const leagueOverview = useLeagueOverview();
  const effectiveValueBasis = (
    source === 'league_war'
      ? warBasis
      : source
  ) as ValueBasis;
  const effectiveLeagueId = (
    source === 'league_war'
      ? leagueId || undefined
      : undefined
  );
  const needsLeagueSelection = (
    source === 'league_war'
  );
  const canRequestBoard = (
    !needsLeagueSelection
    || leagueId.length > 0
  );

  const tiers = usePlayerTiers(
    effectiveValueBasis,
    effectiveLeagueId,
    canRequestBoard,
  );

  const selectedLeagueName = useMemo(
    () =>
      leagueOverview.data.find(
        (league) => league.league_id === leagueId,
      )?.league_name ?? null,
    [
      leagueId,
      leagueOverview.data,
    ],
  );
  const tierBoard = tiers.data;

  return (
    <div className="tiers-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Rankings</p>
          <h1 className="page-title">Player tier board</h1>
          <p className="page-description">
            Visual player tiers across your current value systems, with
            canonical global WAR and optional league-context WAR.
          </p>
        </div>

        <div className="tiers-toolbar">
          <label className="waivers-value-selector">
            <span>Source</span>

            <select
              value={source}
              onChange={(event) => {
                setSource(
                  event.target.value as TierBoardSource,
                );
              }}
            >
              {
                TIER_SOURCE_OPTIONS.map((option) => (
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
            needsLeagueSelection
              ? (
                <>
                  <label className="waivers-value-selector">
                    <span>League</span>

                    <select
                      value={leagueId}
                      onChange={(event) => {
                        setLeagueId(
                          event.target.value,
                        );
                      }}
                    >
                      <option value="">
                        Select a league
                      </option>

                      {
                        leagueOverview.data.map((league) => (
                          <option
                            key={league.league_id}
                            value={league.league_id}
                          >
                            {league.league_name}
                          </option>
                        ))
                      }
                    </select>
                  </label>

                  <label className="waivers-value-selector">
                    <span>WAR Type</span>

                    <select
                      value={warBasis}
                      onChange={(event) => {
                        setWarBasis(
                          event.target.value as ValueBasis,
                        );
                      }}
                    >
                      {
                        WAR_ONLY_OPTIONS.map((option) => (
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
                </>
              )
              : null
          }
        </div>
      </section>

      {
        needsLeagueSelection && !leagueOverview.loading && leagueOverview.data.length === 0
          ? (
            <div className="tiers-empty-state">
              Link a Sleeper account to use league-context WAR tiers.
            </div>
          )
          : null
      }

      {
        needsLeagueSelection && !canRequestBoard
          ? (
            <div className="tiers-empty-state">
              Select one of your leagues to build a league-context WAR board.
            </div>
          )
          : null
      }

      {
        canRequestBoard && tiers.loading
          ? (
            <div className="tiers-empty-state">
              Building tier board...
            </div>
          )
          : null
      }

      {
        canRequestBoard && !tiers.loading && tiers.error
          ? (
            <div className="tiers-empty-state">
              Unable to load the tier board.
            </div>
          )
          : null
      }

      {
        canRequestBoard && tierBoard
          ? (
            <>
              <section className="tiers-meta-row">
                <div className="tiers-meta-block">
                  <span>Value basis</span>
                  <strong>{tierBoard.value_label}</strong>
                </div>

                <div className="tiers-meta-block">
                  <span>Board context</span>
                  <strong>
                    {
                      tierBoard.war_context === 'league'
                        ? selectedLeagueName ?? tierBoard.war_league_name ?? 'Selected league'
                        : 'Global 12-team superflex'
                    }
                  </strong>
                </div>

                <div className="tiers-meta-block">
                  <span>Season</span>
                  <strong>{tierBoard.season}</strong>
                </div>
              </section>

              <section className="tiers-board">
                {
                  tierBoard.tiers.map((tier) => (
                    <div
                      key={tier.label}
                      className="tier-row"
                    >
                      <div className="tier-row-label">
                        <span className="tier-row-grade">
                          {tier.label}
                        </span>

                        <span className="tier-row-count">
                          {tier.players.length}
                        </span>
                      </div>

                      <div className="tier-row-players">
                        {
                          tier.players.length > 0
                            ? tier.players.map((player) => (
                                <article
                                  key={player.player_id}
                                  className="tier-player"
                                  style={{
                                    borderLeftColor: getPositionColor(
                                      player.position,
                                    ),
                                  }}
                                >
                                  <div className="tier-player-main">
                                    <div className="player-with-avatar">
                                      <PlayerAvatar
                                        playerId={player.player_id}
                                        name={player.name}
                                        size="md"
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
                                  </div>

                                  <div className="tier-player-metrics">
                                    <strong>
                                      {
                                        formatSelectedValue(
                                          player,
                                          tierBoard.value_basis,
                                        )
                                      }
                                    </strong>
                                    {
                                      formatExposure(player)
                                        ? (
                                          <small
                                            className={
                                              `tier-player-exposure tier-player-exposure--${getExposureTone(player)}`
                                            }
                                          >
                                            Exposure {formatExposure(player)}
                                          </small>
                                        )
                                        : null
                                    }
                                  </div>
                                </article>
                              ))
                            : (
                              <div className="tier-row-empty">
                                No players in this value band
                              </div>
                            )
                        }
                      </div>
                    </div>
                  ))
                }
              </section>
            </>
          )
          : null
      }
    </div>
  );
};
