import {
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
import { Skeleton } from '@/components/feedback/Skeleton';

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
  createLeagueSelection,
  type BulkTradeLeagueSelection,
} from './BulkTradeLeagueRow';
import { BulkTradeReviewModal } from './BulkTradeReviewModal';
import { TradeSideCard, type TradeSideAsset } from '@/components/trades/TradeSideCard';
import { TradeWinningBar } from '@/components/trades/TradeWinningBar';
import { useValuePreference } from '@/context/useValuePreference';
import type { TradeCalculatorBulkOfferSeed } from './TradeCalculatorTab';


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


function BulkTradeAvailabilitySkeleton() {
  return (
    <section
      className="bulk-trade-league-list bulk-trade-league-list-skeleton"
      role="status"
      aria-live="polite"
    >
      <span className="skeleton-sr-label">
        Checking league ownership and counterparty inventory...
      </span>
      {
        Array.from({ length: 5 }).map((_, index) => (
          <div className="bulk-trade-league-row" key={index}>
            <Skeleton width={16} height={16} radius={4} />

            <div className="bulk-trade-league-primary">
              <div className="bulk-trade-league-identity">
                <Skeleton width={34} height={34} radius={4} />
                <div>
                  <Skeleton width={170} variant="title" />
                  <Skeleton width={120} variant="text" />
                </div>
              </div>
            </div>

            <Skeleton width={132} height={38} />
            <Skeleton width={180} height={38} />
            <Skeleton width={31} height={31} />
          </div>
        ))
      }
    </section>
  );
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

  const [sendPlayers, setSendPlayers] = useState<BulkTradePlayerSearchResult[]>([]);
  const [sendPicks, setSendPicks] = useState<BulkTradePickRequest[]>([]);
  const [receivePlayers, setReceivePlayers] = useState<BulkTradePlayerSearchResult[]>([]);
  const [receivePicks, setReceivePicks] = useState<BulkTradePickRequest[]>([]);
  const [selectionsByLeagueId, setSelectionsByLeagueId] = useState<Record<string, BulkTradeLeagueSelection>>({});
  const [isReviewOpen, setIsReviewOpen] = useState(false);

  const { preference } = useValuePreference();
  const valueBasis = preference === 'fantasycalc' ? 'fantasycalc' : 'ktc';

  const sendPlayerAssets: TradeSideAsset[] = useMemo(() => [
    ...sendPlayers.map((p) => ({
      id: `player-${p.player_id}`,
      type: 'player' as const,
      label: p.name,
      meta: [p.position, p.team, p.age != null ? `${p.age} y.o.` : null].filter(Boolean).join(' · '),
      value: (valueBasis === 'ktc' ? p.ktc_value : p.fc_value) ?? 0,
      position: p.position,
      team: p.team,
      age: p.age,
      playerId: p.player_id,
      underdogRank: p.underdog_position_rank,
    })),
    ...sendPicks.map((pick, index) => ({
      id: `pick-${pick.season}-${pick.round}-${index}`,
      type: 'pick' as const,
      label: `${pick.season} Round ${pick.round}`,
      meta: 'Draft pick',
      value: 0,
      position: 'PICK',
    })),
  ], [sendPlayers, sendPicks, valueBasis]);

  const receivePlayerAssets: TradeSideAsset[] = useMemo(() => [
    ...receivePlayers.map((p) => ({
      id: `player-${p.player_id}`,
      type: 'player' as const,
      label: p.name,
      meta: [p.position, p.team, p.age != null ? `${p.age} y.o.` : null].filter(Boolean).join(' · '),
      value: (valueBasis === 'ktc' ? p.ktc_value : p.fc_value) ?? 0,
      position: p.position,
      team: p.team,
      age: p.age,
      playerId: p.player_id,
      underdogRank: p.underdog_position_rank,
    })),
    ...receivePicks.map((pick, index) => ({
      id: `pick-${pick.season}-${pick.round}-${index}`,
      type: 'pick' as const,
      label: `${pick.season} Round ${pick.round}`,
      meta: 'Draft pick',
      value: 0,
      position: 'PICK',
    })),
  ], [receivePlayers, receivePicks, valueBasis]);

  const sendTotal = useMemo(
    () => sendPlayerAssets.reduce((sum, a) => sum + a.value, 0),
    [sendPlayerAssets],
  );
  const receiveTotal = useMemo(
    () => receivePlayerAssets.reduce((sum, a) => sum + a.value, 0),
    [receivePlayerAssets],
  );

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
    const data = availability.data;

    if (!data) {
      setSelectionsByLeagueId({});
      return;
    }

    setSelectionsByLeagueId(
      Object.fromEntries(
        data.leagues.map((league: BulkTradeLeagueAvailability) => [
          league.league_id,
          createLeagueSelection(
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
      if (!league.is_eligible) {
        return [];
      }

      const selection = selectionsByLeagueId[league.league_id];

      if (!selection?.selected) {
        return [];
      }

      return league.counterparty_options.flatMap(
        (counterparty) => {
          const counterSelection = selection.counterparties[
            counterparty.roster_id
          ];

          if (!counterSelection?.selected) {
            return [];
          }

          const selectedSendPicks = resolveSelectedPicks(
            counterparty.send_pick_choices,
            counterSelection.sendPickOgRosterIdsByRequestIndex,
          );
          const selectedReceivePicks = resolveSelectedPicks(
            counterparty.receive_pick_choices,
            counterSelection.receivePickOgRosterIdsByRequestIndex,
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
              expires_at: null,
            } satisfies BulkTradeOfferRequest,
          ];
        },
      );
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

      const counterparty = getCounterpartyByRosterId(
        league,
        offer.counterparty_roster_id,
      );

      if (!counterparty) {
        return [];
      }

      const counterSelection =
        selectionsByLeagueId[league.league_id]?.counterparties[
          offer.counterparty_roster_id
        ];

      const selectedSendPicks = resolveSelectedPicks(
        counterparty.send_pick_choices,
        counterSelection?.sendPickOgRosterIdsByRequestIndex ?? {},
      );
      const selectedReceivePicks = resolveSelectedPicks(
        counterparty.receive_pick_choices,
        counterSelection?.receivePickOgRosterIdsByRequestIndex ?? {},
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

  const eligibleLeagues = (
    availability.data?.leagues.filter(
      (league: BulkTradeLeagueAvailability) => league.is_eligible,
    ) ?? []
  );

  const eligibleCount = eligibleLeagues.length;

  const selectedCount = offers.length;

  const allSelected =
    eligibleCount > 0
    && eligibleLeagues.every(
      (league: BulkTradeLeagueAvailability) =>
        selectionsByLeagueId[league.league_id]?.selected,
    );

  const handleReset = () => {
    setSendPlayers([]);
    setSendPicks([]);
    setReceivePlayers([]);
    setReceivePicks([]);
    setSelectionsByLeagueId({});
    setIsReviewOpen(false);
    reset();
  };

  const handleGlobalSelectAll = () => {
    if (!availability.data) return;
    setSelectionsByLeagueId(current => {
      const next = { ...current };
      for (const league of eligibleLeagues) {
        const existing = next[league.league_id] ?? createLeagueSelection(league);
        next[league.league_id] = {
          ...existing,
          selected: true,
          counterparties: Object.fromEntries(
            Object.entries(existing.counterparties).map(
              ([id, c]) => [id, { ...c, selected: true }],
            ),
          ),
        };
      }
      return next;
    });
  };

  const handleGlobalSelectNone = () => {
    if (!availability.data) return;
    setSelectionsByLeagueId(current => {
      const next = { ...current };
      for (const league of eligibleLeagues) {
        const existing = next[league.league_id] ?? createLeagueSelection(league);
        next[league.league_id] = {
          ...existing,
          selected: false,
          counterparties: Object.fromEntries(
            Object.entries(existing.counterparties).map(
              ([id, c]) => [id, { ...c, selected: false }],
            ),
          ),
        };
      }
      return next;
    });
  };


  const handleSubmit = (
    expiresInSecs: number | null,
    sendDm: boolean,
  ) => {
    if (offers.length === 0) {
      return;
    }

    const expiresAt =
      expiresInSecs != null
        ? Math.floor(Date.now() / 1000) + expiresInSecs
        : null;

    submitOffers({
      offers: offers.map(offer => ({
        ...offer,
        expires_at: expiresAt,
        send_dm: sendDm,
      })),
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

      <div className="trade-calculator-two-column-grid">
        <TradeSideCard
          title="You send..."
          side="team-a"
          assets={sendPlayerAssets}
          totalValue={sendTotal}
          netValue={sendTotal}
          onAddPlayer={(player) => {
            setSendPlayers((current) => dedupePlayers([...current, player]));
            setSelectionsByLeagueId({});
            reset();
          }}
          onAddPick={(season, round) => {
            setSendPicks((current) => dedupePicks([...current, { season, round }]));
            setSelectionsByLeagueId({});
            reset();
          }}
          onRemoveAsset={(assetId) => {
            if (assetId.startsWith('player-')) {
              const pid = assetId.replace('player-', '');
              setSendPlayers((current) => current.filter((p) => p.player_id !== pid));
            } else {
              const match = assetId.match(/^pick-(.+?)-(\d+)-(\d+)$/);
              if (match) {
                const idx = Number(match[3]);
                setSendPicks((current) => current.filter((_, i) => i !== idx));
              }
            }
            setSelectionsByLeagueId({});
            reset();
          }}
          valueBasis={valueBasis}
          searchPlaceholder="Search player or pick to send..."
          validPickYears={validPickYears}
        />

        <TradeSideCard
          title="You receive..."
          side="team-b"
          assets={receivePlayerAssets}
          totalValue={receiveTotal}
          netValue={receiveTotal}
          onAddPlayer={(player) => {
            setReceivePlayers((current) => dedupePlayers([...current, player]));
            setSelectionsByLeagueId({});
            reset();
          }}
          onAddPick={(season, round) => {
            setReceivePicks((current) => dedupePicks([...current, { season, round }]));
            setSelectionsByLeagueId({});
            reset();
          }}
          onRemoveAsset={(assetId) => {
            if (assetId.startsWith('player-')) {
              const pid = assetId.replace('player-', '');
              setReceivePlayers((current) => current.filter((p) => p.player_id !== pid));
            } else {
              const match = assetId.match(/^pick-(.+?)-(\d+)-(\d+)$/);
              if (match) {
                const idx = Number(match[3]);
                setReceivePicks((current) => current.filter((_, i) => i !== idx));
              }
            }
            setSelectionsByLeagueId({});
            reset();
          }}
          valueBasis={valueBasis}
          searchPlaceholder="Search player or pick to receive..."
          validPickYears={validPickYears}
        />
      </div>

      {(sendPlayerAssets.length > 0 || receivePlayerAssets.length > 0) ? (
        <TradeWinningBar
          teamAName="You send"
          teamBName="You receive"
          teamANet={sendTotal}
          teamBNet={receiveTotal}
        />
      ) : null}


      {
        (sendPlayers.length > 0
          || sendPicks.length > 0
          || receivePlayers.length > 0
          || receivePicks.length > 0)
        && availability.loading
          ? (
            <BulkTradeAvailabilitySkeleton />
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
                <div className="bulk-trade-list-header-left">
                  <strong>
                    {eligibleCount} eligible league{eligibleCount === 1 ? '' : 's'}
                  </strong>

                  <div className="bulk-trade-global-actions">
                    <button
                      className="bulk-trade-select-all"
                      type="button"
                      disabled={allSelected || eligibleCount === 0}
                      onClick={handleGlobalSelectAll}
                    >
                      Select all
                    </button>

                    <button
                      className="bulk-trade-select-none"
                      type="button"
                      disabled={selectedCount === 0}
                      onClick={handleGlobalSelectNone}
                    >
                      Select none
                    </button>
                  </div>
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
                          ?? createLeagueSelection(
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
              receivePlayers={receivePlayers}
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
