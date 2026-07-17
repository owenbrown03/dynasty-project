import './AuctionDraftPage.css';

import { AxiosError } from 'axios';
import {
  Search,
  Wallet,
  CircleDollarSign,
  Gavel,
  Users,
} from 'lucide-react';
import {
  useDeferredValue,
  useMemo,
  useState,
} from 'react';
import { useSearchParams } from 'react-router';

import { LoadingState } from '@/components/feedback/LoadingState';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { ValueBasisSelector } from '@/pages/waivers/ValueBasisSelector';
import { useValuePreference } from '@/context/useValuePreference';
import { useAuctionDraftCenter } from '@/hooks/sleeper/useAuctionDraft';
import { notify } from '@/utils/notify';
import { getPositionColor } from '@/utils/positions';


function formatCurrency(
  value: number | null | undefined,
) {
  if (value == null) {
    return '--';
  }

  return `$${Math.round(value).toLocaleString()}`;
}


function formatValue(
  value: number | null | undefined,
) {
  if (value == null) {
    return '--';
  }

  return value.toFixed(2);
}


export const AuctionDraftPage = () => {
  const valuePreference = useValuePreference();
  const valueBasis = valuePreference.preference;
  const [searchParams, setSearchParams] = useSearchParams();
  const [draftIdInput, setDraftIdInput] = useState(
    searchParams.get('draft_id') ?? '',
  );

  const draftId = (
    searchParams.get('draft_id')
    ?? undefined
  );
  const page = Number(
    searchParams.get('page') ?? '1',
  );
  const pageSize = Number(
    searchParams.get('page_size') ?? '75',
  );
  const search = searchParams.get('search') ?? '';
  const deferredSearch = useDeferredValue(
    search,
  );

  const {
    data,
    loading,
    fetching,
    error,
  } = useAuctionDraftCenter(
    draftId,
    valueBasis,
    deferredSearch,
    page,
    pageSize,
  );

  const totalPages = useMemo(() => {
    if (!data) {
      return 1;
    }

    return Math.max(
      1,
      Math.ceil(
        data.total_available_players
        / data.page_size,
      ),
    );
  }, [data]);

  const applyParams = (
    next: Record<string, string | undefined>,
  ) => {
    const params = new URLSearchParams(
      searchParams,
    );

    Object.entries(next).forEach(
      ([key, value]) => {
        if (value == null || value === '') {
          params.delete(key);
          return;
        }

        params.set(key, value);
      },
    );

    setSearchParams(params);
  };

  const submitDraftId = () => {
    if (!draftIdInput.trim()) {
      notify.error(
        'Enter a Sleeper draft id.',
      );
      return;
    }

    applyParams({
      draft_id: draftIdInput.trim(),
      page: '1',
    });
  };

  const err = error as AxiosError<{
    detail?: string;
  }> | null;

  return (
    <div className="auction-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">
            AUCTION CENTER
          </p>

          <h1 className="page-title">
            Price the room live
          </h1>

          <p className="page-description">
            Enter a Sleeper auction draft id to
            track your buys, roster-construction
            pacing, and live player prices under
            your selected value system.
          </p>
        </div>
      </section>

      <section className="card auction-controls">
        <label className="auction-draft-id">
          <span>Draft id</span>

          <div className="auction-draft-id-row">
            <input
              value={draftIdInput}
              onChange={(event) => {
                setDraftIdInput(
                  event.target.value,
                );
              }}
              placeholder="Paste Sleeper draft id"
            />

            <button
              type="button"
              className="site-button site-button-primary"
              onClick={submitDraftId}
            >
              Load draft
            </button>
          </div>
        </label>

        <ValueBasisSelector
          valueBasis={valueBasis}
          onChange={(nextValueBasis) => {
            valuePreference.setPreference(
              nextValueBasis,
            );
          }}
        />
      </section>

      {!draftId ? (
        <section className="card auction-empty">
          Paste a Sleeper auction draft id to
          load the draft center.
        </section>
      ) : loading ? (
        <LoadingState
          label="Loading live auction board…"
          className="auction-loading"
        />
      ) : err ? (
        <section className="card auction-empty">
          {err.response?.data?.detail
            ?? err.message
            ?? 'Failed to load the auction draft.'}
        </section>
      ) : data ? (
        <>
          <section className="card auction-summary">
            <div className="auction-summary-heading">
              <div>
                <p className="auction-summary-label">
                  {data.season} auction
                </p>
                <h2>{data.league_name}</h2>
                <p>
                  Live pricing by {data.value_label}
                </p>
              </div>

              {fetching ? (
                <span className="auction-refreshing">
                  Refreshing…
                </span>
              ) : null}
            </div>

            <div className="auction-summary-grid">
              <div className="auction-stat">
                <Wallet size={18} />
                <span>Your budget left</span>
                <strong>
                  {formatCurrency(
                    data.my_team.remaining_budget,
                  )}
                </strong>
                <small>
                  Max bid {formatCurrency(
                    data.my_team.max_bid,
                  )}
                </small>
              </div>

              <div className="auction-stat">
                <CircleDollarSign
                  size={18}
                />
                <span>Your spend</span>
                <strong>
                  {formatCurrency(
                    data.my_team.spent_amount,
                  )}
                </strong>
                <small>
                  {data.my_team.spent_budget_pct.toFixed(
                    1,
                  )}
                  % of budget
                </small>
              </div>

              <div className="auction-stat">
                <Gavel size={18} />
                <span>Room spent</span>
                <strong>
                  {formatCurrency(
                    data.spent_budget,
                  )}
                </strong>
                <small>
                  {formatCurrency(
                    data.remaining_budget,
                  )}{' '}
                  remaining
                </small>
              </div>

              <div className="auction-stat">
                <Users size={18} />
                <span>Roster pace</span>
                <strong>
                  {data.my_team.players_drafted}
                  /
                  {data.my_team.roster_size_target}
                </strong>
                <small>
                  {data.my_team.roster_spots_left}{' '}
                  spots left
                </small>
              </div>
            </div>
          </section>

          <section className="auction-grid">
            <div className="auction-column">
              <section className="card auction-panel">
                <div className="auction-panel-heading">
                  <div>
                    <p className="auction-summary-label">
                      Your team
                    </p>
                    <h3>{data.my_team.owner_name}</h3>
                  </div>

                  <div className="auction-panel-value">
                    <span>
                      Bought value
                    </span>
                    <strong>
                      {formatValue(
                        data.my_team.acquired_value,
                      )}
                    </strong>
                  </div>
                </div>

                <div className="auction-position-table">
                  {data.my_team.position_summaries.map(
                    (summary) => (
                      <div
                        key={summary.position}
                        className="auction-position-row"
                      >
                        <strong
                          style={{
                            color: getPositionColor(
                              summary.position,
                            ),
                          }}
                        >
                          {summary.position}
                        </strong>
                        <span>
                          {summary.drafted_count}
                          /
                          {summary.target_count}
                        </span>
                        <span>
                          {formatCurrency(
                            summary.spent_amount,
                          )}
                        </span>
                        <span>
                          {formatValue(
                            summary.selected_value_total,
                          )}
                        </span>
                      </div>
                    ),
                  )}
                </div>

                <div className="auction-drafted-list">
                  {data.my_team.drafted_players.map(
                    (player) => (
                      <article
                        key={player.player_id}
                        className="auction-player-row"
                      >
                        <div className="auction-player-main">
                          <PlayerAvatar
                            playerId={player.player_id}
                            name={player.name}
                            size="md"
                          />

                          <div>
                            <h4>{player.name}</h4>
                            <p>
                              <span
                                style={{
                                  color: getPositionColor(
                                    player.position,
                                  ),
                                }}
                              >
                                {player.position ?? '--'}
                              </span>
                              {' · '}
                              {player.team ?? '--'}
                              {' · '}
                              {player.underdog_position_rank
                                ?? 'UD --'}
                            </p>
                          </div>
                        </div>

                        <div className="auction-player-meta">
                          <strong>
                            {formatCurrency(
                              player.amount_paid,
                            )}
                          </strong>
                          <span>
                            {player.budget_pct.toFixed(
                              1,
                            )}
                            % budget
                          </span>
                          <span>
                            {data.value_label}:{' '}
                            {formatValue(
                              player.selected_value,
                            )}
                          </span>
                        </div>
                      </article>
                    ),
                  )}
                </div>
              </section>
            </div>

            <div className="auction-column">
              <section className="card auction-panel">
                <div className="auction-panel-heading">
                  <div>
                    <p className="auction-summary-label">
                      Room table
                    </p>
                    <h3>
                      Spend and value by team
                    </h3>
                  </div>
                </div>

                <div className="auction-room-table">
                  <div className="auction-room-header">
                    <span>Team</span>
                    <span>Spent</span>
                    <span>Value</span>
                    <span>Max bid</span>
                  </div>

                  {data.team_summaries.map(
                    (team) => (
                      <div
                        key={team.roster_id}
                        className="auction-room-row"
                      >
                        <div>
                          <strong>
                            {team.owner_name}
                          </strong>
                          <small>
                            {team.players_drafted}{' '}
                            bought ·{' '}
                            {team.roster_spots_left}{' '}
                            left
                          </small>
                        </div>
                        <span>
                          {formatCurrency(
                            team.spent_amount,
                          )}
                        </span>
                        <span>
                          {formatValue(
                            team.acquired_value,
                          )}
                        </span>
                        <span>
                          {formatCurrency(
                            team.max_bid,
                          )}
                        </span>
                      </div>
                    ),
                  )}
                </div>
              </section>
            </div>
          </section>

          <section className="card auction-panel">
            <div className="auction-panel-heading auction-available-heading">
              <div>
                <p className="auction-summary-label">
                  Available players
                </p>
                <h3>
                  Suggested live prices
                </h3>
              </div>

              <div className="auction-available-controls">
                <label className="auction-search">
                  <Search size={14} />
                  <input
                    value={search}
                    onChange={(event) => {
                      applyParams({
                        search: event.target.value,
                        page: '1',
                      });
                    }}
                    placeholder="Search players"
                  />
                </label>

                <label className="auction-page-size">
                  <span>Rows</span>
                  <select
                    value={pageSize}
                    onChange={(event) => {
                      applyParams({
                        page_size:
                          event.target.value,
                        page: '1',
                      });
                    }}
                  >
                    {[50, 75, 100, 150].map(
                      (size) => (
                        <option
                          key={size}
                          value={size}
                        >
                          {size}
                        </option>
                      ),
                    )}
                  </select>
                </label>
              </div>
            </div>

            <div className="auction-available-table">
              <div className="auction-available-header">
                <span>Player</span>
                <span>{data.value_label}</span>
                <span>Fair</span>
                <span>Your max</span>
              </div>

              {data.available_players.map(
                (player) => (
                  <div
                    key={player.player_id}
                    className="auction-available-row"
                  >
                    <div className="auction-player-main">
                      <PlayerAvatar
                        playerId={player.player_id}
                        name={player.name}
                        size="md"
                      />

                      <div>
                        <h4>{player.name}</h4>
                        <p>
                          <span
                            style={{
                              color: getPositionColor(
                                player.position,
                              ),
                            }}
                          >
                            {player.position ?? '--'}
                          </span>
                          {' · '}
                          {player.team ?? '--'}
                          {' · '}
                          {player.underdog_position_rank
                            ?? 'UD --'}
                        </p>
                      </div>
                    </div>

                    <span>
                      {formatValue(
                        player.selected_value,
                      )}
                    </span>
                    <span>
                      {formatCurrency(
                        player.fair_market_price,
                      )}
                    </span>
                    <span>
                      {formatCurrency(
                        player.suggested_max_bid,
                      )}
                    </span>
                  </div>
                ),
              )}
            </div>

            <div className="auction-pagination">
              <button
                type="button"
                className="site-button"
                onClick={() => {
                  applyParams({
                    page: String(
                      Math.max(
                        page - 1,
                        1,
                      ),
                    ),
                  });
                }}
                disabled={page <= 1}
              >
                Previous
              </button>

              <span>
                Page {page} of {totalPages}
              </span>

              <button
                type="button"
                className="site-button"
                onClick={() => {
                  applyParams({
                    page: String(
                      Math.min(
                        page + 1,
                        totalPages,
                      ),
                    ),
                  });
                }}
                disabled={page >= totalPages}
              >
                Next
              </button>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
};
