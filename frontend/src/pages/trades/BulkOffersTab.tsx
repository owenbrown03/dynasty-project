import {
  LoaderCircle,
  RotateCcw,
  Send,
} from 'lucide-react';
import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import {
  useBulkTradeAvailability,
  useSubmitBulkTradeOffers,
} from '@/hooks/sleeper/useBulkTrades';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

import type {
  BulkTradeCounterparty,
  BulkTradeLeagueAvailability,
  TradeDraftPickAsset,
  BulkTradeOfferRequest,
  BulkTradePlayerSearchResult,
  TradeDirection,
} from '@/types';

import {
  BulkTradeLeagueRow,
  type BulkTradeLeagueSelection,
} from './BulkTradeLeagueRow';
import { BulkTradePlayerSearch } from './BulkTradePlayerSearch';
import { BulkTradeReviewModal } from './BulkTradeReviewModal';


const DEFAULT_PICK_SEASON = '2027';
const DEFAULT_PICK_ROUND = 2;
const ROOKIE_DRAFT_ROLLOVER_MONTH = 5;
const ROOKIE_DRAFT_ROLLOVER_DAY = 1;


function getValidSleeperPickYears(
  now = new Date(),
): string[] {
  const currentYear = now.getFullYear();
  const rookieDraftRollover = new Date(
    currentYear,
    ROOKIE_DRAFT_ROLLOVER_MONTH,
    ROOKIE_DRAFT_ROLLOVER_DAY,
  );

  const startYear = (
    now >= rookieDraftRollover
      ? currentYear + 1
      : currentYear
  );

  return Array.from(
    {
      length: 3,
    },
    (_, index) => String(startYear + index),
  );
}


function createInitialSelection(
  league: BulkTradeLeagueAvailability,
  direction: TradeDirection,
): BulkTradeLeagueSelection {
  if (!league.is_eligible) {
    return {
      selected: false,
      counterpartyRosterId: null,
      pickOgRosterId: null,
    };
  }

  if (direction === 'buy') {
    return {
      selected: true,
      counterpartyRosterId: (
        league.target_owner_roster_id
      ),
      pickOgRosterId: (
        league.matching_picks[0]
          ?.og_roster_id
        ?? null
      ),
    };
  }

  const firstCounterparty = (
    league.counterparty_options[0]
  );

  return {
    selected: true,
    counterpartyRosterId: (
      firstCounterparty?.roster_id
      ?? null
    ),
    pickOgRosterId: (
      firstCounterparty?.matching_picks[0]
        ?.og_roster_id
      ?? null
    ),
  };
}


function getSelectedPick(
  league: BulkTradeLeagueAvailability,
  selection: BulkTradeLeagueSelection,
  direction: TradeDirection,
): TradeDraftPickAsset | null {
  if (direction === 'buy') {
    return league.matching_picks.find(
      pick => (
        pick.og_roster_id
        === selection.pickOgRosterId
      ),
    ) ?? null;
  }

  const counterparty = (
    league.counterparty_options.find(
      (option: BulkTradeCounterparty) => (
        option.roster_id
        === selection.counterpartyRosterId
      ),
    )
  );

  return counterparty?.matching_picks.find(
    pick => (
      pick.og_roster_id
      === selection.pickOgRosterId
    ),
  ) ?? null;
}


export const BulkOffersTab = () => {
  const {
    canWrite,
  } = useSleeperConnection();
  const validPickYears = useMemo(
    () => getValidSleeperPickYears(),
    [],
  );

  const [direction, setDirection] = useState<
    TradeDirection
  >('buy');

  const [pickSeason, setPickSeason] = useState(
    validPickYears[0]
    ?? DEFAULT_PICK_SEASON,
  );

  const [pickRound, setPickRound] = useState(
    DEFAULT_PICK_ROUND,
  );

  const [selectedPlayer, setSelectedPlayer] = useState<
    BulkTradePlayerSearchResult | null
  >(null);

  const [selectionsByLeagueId, setSelectionsByLeagueId] = (
    useState<
      Record<
        string,
        BulkTradeLeagueSelection
      >
    >({})
  );

  const [isReviewOpen, setIsReviewOpen] = useState(
    false,
  );

  const availability = useBulkTradeAvailability(
    selectedPlayer?.player_id,
    direction,
    pickSeason,
    pickRound,
  );

  const {
    submitOffers,
    submitting,
    results,
    error: submitError,
    reset,
  } = useSubmitBulkTradeOffers();

  useEffect(() => {
    if (
      !validPickYears.includes(pickSeason)
    ) {
      setPickSeason(
        validPickYears[0]
        ?? DEFAULT_PICK_SEASON,
      );
    }
  }, [
    pickSeason,
    validPickYears,
  ]);

  useEffect(() => {
    const data = availability.data;

    if (!data) {
      setSelectionsByLeagueId({});
      return;
    }

    setSelectionsByLeagueId(
      Object.fromEntries(
        data.leagues.map((league: BulkTradeLeagueAvailability) => [
          league.league_id,
          createInitialSelection(
            league,
            direction,
          ),
        ]),
      ),
    );
  }, [
    availability.data,
    direction,
  ]);

  const offers = useMemo(() => {
    const data = availability.data;

    if (!data || !selectedPlayer) {
      return [];
    }

    return data.leagues.flatMap((league: BulkTradeLeagueAvailability) => {
      const selection = selectionsByLeagueId[
        league.league_id
      ];

      if (
        !league.is_eligible
        || !selection?.selected
        || selection.counterpartyRosterId === null
      ) {
        return [];
      }

      const pick = getSelectedPick(
        league,
        selection,
        direction,
      );

      if (!pick) {
        return [];
      }

      return [
        {
          league_id: league.league_id,
          your_roster_id: league.your_roster_id,
          counterparty_roster_id: (
            selection.counterpartyRosterId
          ),
          target_player_id: selectedPlayer.player_id,
          direction,
          pick: {
            season: pick.season,
            round: pick.round,
            og_roster_id: pick.og_roster_id,
          },
        } satisfies BulkTradeOfferRequest,
      ];
    });
  }, [
    availability.data,
    direction,
    selectedPlayer,
    selectionsByLeagueId,
  ]);

  const reviewOffers = useMemo(() => {
    const data = availability.data;

    if (!data) {
      return [];
    }

    return offers.flatMap(offer => {
      const league = data.leagues.find(
        item => item.league_id === offer.league_id,
      );

      if (!league) {
        return [];
      }

      const selection = selectionsByLeagueId[
        league.league_id
      ];

      const pick = getSelectedPick(
        league,
        selection,
        direction,
      );

      const counterpartyName = (
        direction === 'buy'
          ? league.target_owner_name
          : league.counterparty_options.find(
            (option: BulkTradeCounterparty) => (
              option.roster_id
              === offer.counterparty_roster_id
            ),
          )?.name
      );

      return [
        {
          offer,
          leagueName: league.league_name,
          counterpartyName: (
            counterpartyName
            ?? `Roster ${offer.counterparty_roster_id}`
          ),
          pickLabel: (
            pick?.label
            ?? `${offer.pick.season} Round ${offer.pick.round}`
          ),
        },
      ];
    });
  }, [
    availability.data,
    direction,
    offers,
    selectionsByLeagueId,
  ]);

  const eligibleCount = (
    availability.data?.leagues.filter(
      (league: BulkTradeLeagueAvailability) => league.is_eligible,
    ).length
    ?? 0
  );

  const selectedCount = offers.length;

  const handleDirectionChange = (
    nextDirection: TradeDirection,
  ) => {
    setDirection(nextDirection);
    setSelectionsByLeagueId({});
    reset();
  };

  const handleReset = () => {
    setSelectedPlayer(null);
    setSelectionsByLeagueId({});
    setIsReviewOpen(false);
    reset();
  };

  const handleSubmit = () => {
    if (offers.length === 0) {
      return;
    }

    submitOffers({
      offers,
    });
  };

  return (
    <section className="bulk-offers-tab">
      <div className="bulk-trade-intro">
        <div>
          <span className="page-eyebrow">
            Cross-league offers
          </span>

          <h1>
            Bulk Trade Offers
          </h1>

          <p>
            Build the same player-for-pick offer across
            your leagues, review each one, and send only
            the leagues you select.
          </p>
        </div>

        {
          selectedPlayer
            ? (
              <button
                className="button-secondary"
                onClick={handleReset}
                disabled={submitting}
              >
                <RotateCcw size={15} />
                Reset
              </button>
            )
            : null
        }
      </div>

      <div className="bulk-trade-config-card">
        <div className="bulk-trade-direction-toggle">
          <button
            className={
              direction === 'buy'
                ? 'active'
                : ''
            }
            onClick={() => {
              handleDirectionChange('buy');
            }}
          >
            Buy
          </button>

          <button
            className={
              direction === 'sell'
                ? 'active'
                : ''
            }
            onClick={() => {
              handleDirectionChange('sell');
            }}
          >
            Sell
          </button>
        </div>

        <BulkTradePlayerSearch
          selectedPlayer={selectedPlayer}
          onSelectPlayer={player => {
            setSelectedPlayer(player);
            setSelectionsByLeagueId({});
            reset();
          }}
        />

        <div className="bulk-trade-price-controls">
          <label>
            <span>
              Pick year
            </span>

            <select
              value={pickSeason}
              onChange={event => {
                setPickSeason(
                  event.target.value,
                );
              }}
            >
              {
                validPickYears.map(year => (
                  <option
                    key={year}
                    value={year}
                  >
                    {year}
                  </option>
                ))
              }
            </select>
          </label>

          <label>
            <span>
              Round
            </span>

            <select
              value={pickRound}
              onChange={event => {
                setPickRound(
                  Number(event.target.value),
                );
              }}
            >
              {
                Array.from(
                  {
                    length: 8,
                  },
                  (_, index) => index + 1,
                ).map(round => (
                  <option
                    key={round}
                    value={round}
                  >
                    Round {round}
                  </option>
                ))
              }
            </select>
          </label>

          <div className="bulk-trade-price-summary">
            <span>
              Offer price
            </span>

            <strong>
              {pickSeason || 'YYYY'} Round {pickRound}
            </strong>
          </div>
        </div>
      </div>

      {
        selectedPlayer
        && availability.loading
          ? (
            <div className="bulk-trade-loading">
              <LoaderCircle
                className="trade-spinner"
                size={18}
              />
              Checking league ownership and pick inventory...
            </div>
          )
          : null
      }

      {
        availability.error
          ? (
            <div className="bulk-trade-error">
              {
                availability.error instanceof Error
                  ? availability.error.message
                  : 'Unable to load trade availability.'
              }
            </div>
          )
          : null
      }

      {
        availability.data
          ? (
            <>
              <div className="bulk-trade-list-header">
                <div>
                  <strong>
                    {selectedCount}
                    /
                    {eligibleCount}
                    {' '}
                    eligible leagues selected
                  </strong>

                  <span>
                    {
                      direction === 'buy'
                        ? `Offer ${pickSeason} Round ${pickRound} for ${selectedPlayer?.name}`
                        : `Offer ${selectedPlayer?.name} for a ${pickSeason} Round ${pickRound}`
                    }
                  </span>
                </div>

                <button
                  className="button-secondary bulk-trade-review-button"
                  onClick={() => {
                    setIsReviewOpen(true);
                  }}
                  disabled={
                    !canWrite
                    || selectedCount === 0
                    || submitting
                  }
                  title={
                    !canWrite
                      ? 'Enable Sleeper write access to send trade offers.'
                      : undefined
                  }
                >
                  <Send size={15} />
                  Review {selectedCount} Offer{
                    selectedCount === 1
                      ? ''
                      : 's'
                  }
                </button>
              </div>

              <div className="bulk-trade-league-list">
                {
                  availability.data.leagues.map(
                    league => (
                      <BulkTradeLeagueRow
                        key={league.league_id}
                        league={league}
                        direction={direction}
                        selection={
                          selectionsByLeagueId[
                            league.league_id
                          ]
                          ?? createInitialSelection(
                            league,
                            direction,
                          )
                        }
                        onChange={nextSelection => {
                          setSelectionsByLeagueId(
                            current => ({
                              ...current,
                              [league.league_id]: nextSelection,
                            }),
                          );
                        }}
                      />
                    ),
                  )
                }
              </div>
            </>
          )
          : null
      }

      {
        isReviewOpen
        && selectedPlayer
          ? (
            <BulkTradeReviewModal
              direction={direction}
              player={selectedPlayer}
              offers={reviewOffers}
              submitting={submitting}
              results={results}
              error={submitError}
              onClose={() => {
                setIsReviewOpen(false);

                if (results.length > 0) {
                  reset();
                }
              }}
              onSubmit={handleSubmit}
            />
          )
          : null
      }
    </section>
  );
};
