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
  BulkTradeAvailabilityRequest,
  BulkTradeCounterparty,
  BulkTradeLeagueAvailability,
  BulkTradeOfferRequest,
  BulkTradePickRequest,
  BulkTradePlayerSearchResult,
  TradeDraftPickAsset,
} from '@/types';

import {
  BulkTradeLeagueRow,
  type BulkTradeLeagueSelection,
} from './BulkTradeLeagueRow';
import { BulkTradePlayerSearch } from './BulkTradePlayerSearch';
import { BulkTradeReviewModal } from './BulkTradeReviewModal';
import type { TradeCalculatorBulkOfferSeed } from './TradeCalculatorTab';


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


function dedupePlayers(
  players: BulkTradePlayerSearchResult[],
): BulkTradePlayerSearchResult[] {
  return Array.from(
    new Map(
      players.map(
        player => [
          player.player_id,
          player,
        ],
      ),
    ).values(),
  );
}


function dedupePicks(
  picks: BulkTradePickRequest[],
): BulkTradePickRequest[] {
  return Array.from(
    new Map(
      picks.map(
        pick => [
          `${pick.season}-${pick.round}`,
          pick,
        ],
      ),
    ).values(),
  );
}


function formatPickPackage(
  picks: BulkTradePickRequest[],
): string {
  return picks.map(
    pick => `${pick.season} R${pick.round}`,
  ).join(', ');
}


function buildPickSelectionMap(
  pickChoices: {
    request_index: number;
    matching_picks: TradeDraftPickAsset[];
  }[],
): Record<number, number | null> {
  return Object.fromEntries(
    pickChoices.map(
      pickChoice => [
        pickChoice.request_index,
        pickChoice.matching_picks[0]?.og_roster_id ?? null,
      ],
    ),
  );
}


function createInitialSelection(
  league: BulkTradeLeagueAvailability,
): BulkTradeLeagueSelection {
  if (!league.is_eligible) {
    return {
      selected: false,
      counterpartyRosterId: null,
      sendPickOgRosterIdsByRequestIndex: {},
      receivePickOgRosterIdsByRequestIndex: {},
    };
  }

  const firstCounterparty = league.counterparty_options[0];

  return {
    selected: true,
    counterpartyRosterId: firstCounterparty?.roster_id ?? null,
    sendPickOgRosterIdsByRequestIndex: buildPickSelectionMap(
      firstCounterparty?.send_pick_choices ?? [],
    ),
    receivePickOgRosterIdsByRequestIndex: buildPickSelectionMap(
      firstCounterparty?.receive_pick_choices ?? [],
    ),
  };
}


function getCounterpartyByRosterId(
  league: BulkTradeLeagueAvailability,
  rosterId: number | null,
): BulkTradeCounterparty | null {
  if (rosterId === null) {
    return null;
  }

  return league.counterparty_options.find(
    option => option.roster_id === rosterId,
  ) ?? null;
}


function resolveSelectedPicks(
  pickChoices: {
    request_index: number;
    matching_picks: TradeDraftPickAsset[];
  }[],
  selectionsByRequestIndex: Record<number, number | null>,
): TradeDraftPickAsset[] {
  return pickChoices.flatMap(
    pickChoice => {
      const selectedOgRosterId = selectionsByRequestIndex[
        pickChoice.request_index
      ];

      const pick = pickChoice.matching_picks.find(
        candidate => candidate.og_roster_id === selectedOgRosterId,
      );

      return pick ? [pick] : [];
    },
  );
}


function buildAvailabilityPayload(
  sendPlayers: BulkTradePlayerSearchResult[],
  sendPicks: BulkTradePickRequest[],
  receivePlayers: BulkTradePlayerSearchResult[],
  receivePicks: BulkTradePickRequest[],
): BulkTradeAvailabilityRequest | null {
  if (
    sendPlayers.length + sendPicks.length === 0
    || receivePlayers.length + receivePicks.length === 0
  ) {
    return null;
  }

  return {
    send_player_ids: sendPlayers.map(
      player => player.player_id,
    ),
    send_picks: sendPicks,
    receive_player_ids: receivePlayers.map(
      player => player.player_id,
    ),
    receive_picks: receivePicks,
  };
}


export const BulkOffersTab = ({
  seed,
}: {
  seed?: TradeCalculatorBulkOfferSeed | null;
}) => {
  const {
    canWrite,
  } = useSleeperConnection();
  const validPickYears = useMemo(
    () => getValidSleeperPickYears(),
    [],
  );

  const [sendPickSeason, setSendPickSeason] = useState(validPickYears[0] ?? DEFAULT_PICK_SEASON);
  const [sendPickRound, setSendPickRound] = useState(DEFAULT_PICK_ROUND);
  const [receivePickSeason, setReceivePickSeason] = useState(validPickYears[0] ?? DEFAULT_PICK_SEASON);
  const [receivePickRound, setReceivePickRound] = useState(DEFAULT_PICK_ROUND);

  const [sendPlayers, setSendPlayers] = useState<BulkTradePlayerSearchResult[]>([]);
  const [sendPicks, setSendPicks] = useState<BulkTradePickRequest[]>([]);
  const [receivePlayers, setReceivePlayers] = useState<BulkTradePlayerSearchResult[]>([]);
  const [receivePicks, setReceivePicks] = useState<BulkTradePickRequest[]>([]);
  const [selectionsByLeagueId, setSelectionsByLeagueId] = useState<Record<string, BulkTradeLeagueSelection>>({});
  const [isReviewOpen, setIsReviewOpen] = useState(false);

  const availabilityPayload = useMemo(
    () => buildAvailabilityPayload(
      sendPlayers,
      sendPicks,
      receivePlayers,
      receivePicks,
    ),
    [
      receivePicks,
      receivePlayers,
      sendPicks,
      sendPlayers,
    ],
  );

  const availability = useBulkTradeAvailability(
    availabilityPayload,
  );

  const {
    submitOffers,
    submitting,
    results,
    error: submitError,
    reset,
  } = useSubmitBulkTradeOffers();

  useEffect(() => {
    if (!validPickYears.includes(sendPickSeason)) {
      setSendPickSeason(
        validPickYears[0] ?? DEFAULT_PICK_SEASON,
      );
    }

    if (!validPickYears.includes(receivePickSeason)) {
      setReceivePickSeason(
        validPickYears[0] ?? DEFAULT_PICK_SEASON,
      );
    }
  }, [
    receivePickSeason,
    sendPickSeason,
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
          ),
        ]),
      ),
    );
  }, [
    availability.data,
  ]);

  useEffect(() => {
    if (!seed) {
      return;
    }

    setSendPlayers(
      dedupePlayers(seed.sendPlayers),
    );
    setSendPicks(
      dedupePicks(seed.sendPicks),
    );
    setReceivePlayers(
      dedupePlayers(seed.receivePlayers),
    );
    setReceivePicks(
      dedupePicks(seed.receivePicks),
    );
    setSelectionsByLeagueId({});
    setIsReviewOpen(false);
    reset();
  }, [
    reset,
    seed,
  ]);

  const offers = useMemo(() => {
    const data = availability.data;

    if (!data) {
      return [];
    }

    return data.leagues.flatMap((league: BulkTradeLeagueAvailability) => {
      const selection = selectionsByLeagueId[league.league_id];
      const counterparty = getCounterpartyByRosterId(
        league,
        selection?.counterpartyRosterId ?? null,
      );

      if (
        !league.is_eligible
        || !selection?.selected
        || !counterparty
      ) {
        return [];
      }

      const selectedSendPicks = resolveSelectedPicks(
        counterparty.send_pick_choices,
        selection.sendPickOgRosterIdsByRequestIndex,
      );
      const selectedReceivePicks = resolveSelectedPicks(
        counterparty.receive_pick_choices,
        selection.receivePickOgRosterIdsByRequestIndex,
      );

      if (
        selectedSendPicks.length !== sendPicks.length
        || selectedReceivePicks.length !== receivePicks.length
      ) {
        return [];
      }

      return [
        {
          league_id: league.league_id,
          your_roster_id: league.your_roster_id,
          counterparty_roster_id: counterparty.roster_id,
          send_player_ids: sendPlayers.map(
            player => player.player_id,
          ),
          send_picks: selectedSendPicks.map(
            pick => ({
              season: pick.season,
              round: pick.round,
              og_roster_id: pick.og_roster_id,
            }),
          ),
          receive_player_ids: receivePlayers.map(
            player => player.player_id,
          ),
          receive_picks: selectedReceivePicks.map(
            pick => ({
              season: pick.season,
              round: pick.round,
              og_roster_id: pick.og_roster_id,
            }),
          ),
        } satisfies BulkTradeOfferRequest,
      ];
    });
  }, [
    availability.data,
    receivePicks.length,
    receivePlayers,
    selectionsByLeagueId,
    sendPicks.length,
    sendPlayers,
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

      const selection = selectionsByLeagueId[league.league_id];
      const counterparty = getCounterpartyByRosterId(
        league,
        selection?.counterpartyRosterId ?? null,
      );

      if (!counterparty) {
        return [];
      }

      const selectedSendPicks = resolveSelectedPicks(
        counterparty.send_pick_choices,
        selection.sendPickOgRosterIdsByRequestIndex,
      );
      const selectedReceivePicks = resolveSelectedPicks(
        counterparty.receive_pick_choices,
        selection.receivePickOgRosterIdsByRequestIndex,
      );

      return [
        {
          offer,
          leagueName: league.league_name,
          counterpartyName: counterparty.name,
          sendPickLabels: selectedSendPicks.map(
            pick => pick.label,
          ),
          receivePickLabels: selectedReceivePicks.map(
            pick => pick.label,
          ),
        },
      ];
    });
  }, [
    availability.data,
    offers,
    selectionsByLeagueId,
  ]);

  const eligibleCount = (
    availability.data?.leagues.filter(
      (league: BulkTradeLeagueAvailability) => league.is_eligible,
    ).length ?? 0
  );

  const selectedCount = offers.length;

  const handleReset = () => {
    setSendPlayers([]);
    setSendPicks([]);
    setReceivePlayers([]);
    setReceivePicks([]);
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
            Build the same mixed asset package across your leagues, review each one, and send only the leagues you select.
          </p>
        </div>

        {
          sendPlayers.length > 0
          || sendPicks.length > 0
          || receivePlayers.length > 0
          || receivePicks.length > 0
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
        <BulkTradePlayerSearch
          label="You send players"
          placeholder="Search a player you want to send..."
          selectedPlayers={sendPlayers}
          onAddPlayer={player => {
            setSendPlayers(current => dedupePlayers([
              ...current,
              player,
            ]));
            setSelectionsByLeagueId({});
            reset();
          }}
          onRemovePlayer={playerId => {
            setSendPlayers(current => current.filter(
              player => player.player_id !== playerId,
            ));
            setSelectionsByLeagueId({});
            reset();
          }}
        />

        <div className="bulk-trade-price-controls">
          <label>
            <span>
              Send pick year
            </span>

            <select
              value={sendPickSeason}
              onChange={event => {
                setSendPickSeason(event.target.value);
              }}
            >
              {
                validPickYears.map(year => (
                  <option
                    key={`send-${year}`}
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
              Send round
            </span>

            <select
              value={sendPickRound}
              onChange={event => {
                setSendPickRound(Number(event.target.value));
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
                    key={`send-round-${round}`}
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
              Send pick package
            </span>

            <strong>
              {sendPicks.length > 0
                ? formatPickPackage(sendPicks)
                : 'None selected'}
            </strong>
          </div>

          <button
            className="button-secondary"
            type="button"
            onClick={() => {
              setSendPicks(current => dedupePicks([
                ...current,
                {
                  season: sendPickSeason,
                  round: sendPickRound,
                },
              ]));
              setSelectionsByLeagueId({});
              reset();
            }}
          >
            Add send pick
          </button>
        </div>

        {
          sendPicks.length > 0
            ? (
              <div className="bulk-trade-search-results">
                {
                  sendPicks.map((pick, index) => (
                    <div
                      key={`send-${pick.season}-${pick.round}-${index}`}
                      className="bulk-trade-selected-player"
                    >
                      <div className="player-with-avatar-copy">
                        <strong>{pick.season} Round {pick.round}</strong>
                        <span>Pick you send</span>
                      </div>

                      <button
                        className="button-secondary"
                        onClick={() => {
                          setSendPicks(current => current.filter(
                            (_, currentIndex) => currentIndex !== index,
                          ));
                          setSelectionsByLeagueId({});
                          reset();
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  ))
                }
              </div>
            )
            : null
        }

        <BulkTradePlayerSearch
          label="You receive players"
          placeholder="Search a player you want to receive..."
          selectedPlayers={receivePlayers}
          onAddPlayer={player => {
            setReceivePlayers(current => dedupePlayers([
              ...current,
              player,
            ]));
            setSelectionsByLeagueId({});
            reset();
          }}
          onRemovePlayer={playerId => {
            setReceivePlayers(current => current.filter(
              player => player.player_id !== playerId,
            ));
            setSelectionsByLeagueId({});
            reset();
          }}
        />

        <div className="bulk-trade-price-controls">
          <label>
            <span>
              Receive pick year
            </span>

            <select
              value={receivePickSeason}
              onChange={event => {
                setReceivePickSeason(event.target.value);
              }}
            >
              {
                validPickYears.map(year => (
                  <option
                    key={`receive-${year}`}
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
              Receive round
            </span>

            <select
              value={receivePickRound}
              onChange={event => {
                setReceivePickRound(Number(event.target.value));
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
                    key={`receive-round-${round}`}
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
              Receive pick package
            </span>

            <strong>
              {receivePicks.length > 0
                ? formatPickPackage(receivePicks)
                : 'None selected'}
            </strong>
          </div>

          <button
            className="button-secondary"
            type="button"
            onClick={() => {
              setReceivePicks(current => dedupePicks([
                ...current,
                {
                  season: receivePickSeason,
                  round: receivePickRound,
                },
              ]));
              setSelectionsByLeagueId({});
              reset();
            }}
          >
            Add receive pick
          </button>
        </div>

        {
          receivePicks.length > 0
            ? (
              <div className="bulk-trade-search-results">
                {
                  receivePicks.map((pick, index) => (
                    <div
                      key={`receive-${pick.season}-${pick.round}-${index}`}
                      className="bulk-trade-selected-player"
                    >
                      <div className="player-with-avatar-copy">
                        <strong>{pick.season} Round {pick.round}</strong>
                        <span>Pick you receive</span>
                      </div>

                      <button
                        className="button-secondary"
                        onClick={() => {
                          setReceivePicks(current => current.filter(
                            (_, currentIndex) => currentIndex !== index,
                          ));
                          setSelectionsByLeagueId({});
                          reset();
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  ))
                }
              </div>
            )
            : null
        }
      </div>

      {
        (sendPlayers.length > 0
          || sendPicks.length > 0
          || receivePlayers.length > 0
          || receivePicks.length > 0)
        && availability.loading
          ? (
            <div className="bulk-trade-loading">
              <LoaderCircle
                className="trade-spinner"
                size={18}
              />
              Checking league ownership and counterparty inventory...
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
                    Send {[
                      ...sendPlayers.map(player => player.name),
                      ...sendPicks.map(pick => `${pick.season} R${pick.round}`),
                    ].join(', ')}
                    {' for '}
                    {[
                      ...receivePlayers.map(player => player.name),
                      ...receivePicks.map(pick => `${pick.season} R${pick.round}`),
                    ].join(', ')}
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
                        selection={
                          selectionsByLeagueId[league.league_id]
                          ?? createInitialSelection(
                            league,
                          )
                        }
                        onChange={nextSelection => {
                          setSelectionsByLeagueId(current => ({
                            ...current,
                            [league.league_id]: nextSelection,
                          }));
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
          ? (
            <BulkTradeReviewModal
              sendPlayers={sendPlayers}
              sendPicks={sendPicks}
              receivePlayers={receivePlayers}
              receivePicks={receivePicks}
              offers={reviewOffers}
              submitting={submitting}
              results={results}
              error={submitError}
              onClose={() => {
                setIsReviewOpen(false);
              }}
              onSubmit={handleSubmit}
            />
          )
          : null
      }
    </section>
  );
};
