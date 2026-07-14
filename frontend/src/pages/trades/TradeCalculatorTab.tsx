import { useMemo, useState } from 'react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import {
  fetchTradeCalculatorPickValue,
  useBulkTradePlayerSearch,
} from '@/hooks/sleeper/useBulkTrades';
import type {
  BulkTradePlayerSearchResult,
  BulkTradePickRequest,
  TradeDirection,
} from '@/types';
import { notify } from '@/utils/notify';


type CalculatorBasis =
  | 'ktc'
  | 'fantasycalc';

type CalculatorSide =
  | 'team-a'
  | 'team-b';

type CalculatorAsset = {
  id: string;
  type: 'player' | 'pick';
  label: string;
  meta: string;
  ktcValue: number | null;
  fcValue: number | null;
  player?: BulkTradePlayerSearchResult;
  pickSeason?: string;
  pickRound?: number;
};

export interface TradeCalculatorBulkOfferSeed {
  direction: TradeDirection;
  players: BulkTradePlayerSearchResult[];
  picks: BulkTradePickRequest[];
}


function getAssetValue(
  asset: CalculatorAsset,
  basis: CalculatorBasis,
) {
  return basis === 'ktc'
    ? asset.ktcValue ?? 0
    : asset.fcValue ?? 0;
}


function formatCalculatorValue(
  value: number,
) {
  return Math.round(value).toLocaleString();
}


function buildPlayerAsset(
  player: BulkTradePlayerSearchResult,
) {
  return {
    id: `player-${player.player_id}`,
    type: 'player' as const,
    label: player.name,
    meta: [
      player.position,
      player.team,
      player.age !== null
        ? `Age ${player.age}`
        : null,
    ]
      .filter(Boolean)
      .join(' · '),
    ktcValue: player.ktc_value,
    fcValue: player.fc_value,
    player,
  };
}

function buildBulkOfferSeed({
  mySide,
  teamAReceives,
  teamBReceives,
}: {
  mySide: CalculatorSide;
  teamAReceives: CalculatorAsset[];
  teamBReceives: CalculatorAsset[];
}): TradeCalculatorBulkOfferSeed | null {
  if (
    teamAReceives.length === 0
    || teamBReceives.length === 0
  ) {
    return null;
  }

  const myAssets = mySide === 'team-a'
    ? teamAReceives
    : teamBReceives;
  const counterpartyAssets = mySide === 'team-a'
    ? teamBReceives
    : teamAReceives;
  const myPlayers = myAssets.filter(
    asset => asset.type === 'player' && asset.player,
  );
  const myPicks = myAssets.filter(
    asset => asset.type === 'pick'
      && asset.pickSeason
      && asset.pickRound,
  );
  const counterpartyPlayers = counterpartyAssets.filter(
    asset => asset.type === 'player' && asset.player,
  );
  const counterpartyPicks = counterpartyAssets.filter(
    asset => asset.type === 'pick'
      && asset.pickSeason
      && asset.pickRound,
  );

  if (
    myPlayers.length === myAssets.length
    && counterpartyPicks.length === counterpartyAssets.length
  ) {
    return {
      direction: 'buy',
      players: myPlayers.map(
        asset => asset.player!,
      ),
      picks: counterpartyPicks.map(
        asset => ({
          season: asset.pickSeason!,
          round: asset.pickRound!,
        }),
      ),
    };
  }

  if (
    myPicks.length === myAssets.length
    && counterpartyPlayers.length === counterpartyAssets.length
  ) {
    return {
      direction: 'sell',
      players: counterpartyPlayers.map(
        asset => asset.player!,
      ),
      picks: myPicks.map(
        asset => ({
          season: asset.pickSeason!,
          round: asset.pickRound!,
        }),
      ),
    };
  }

  return null;
}

export function TradeCalculatorTab({
  onSendToBulkOffers,
}: {
  onSendToBulkOffers?: (
    seed: TradeCalculatorBulkOfferSeed,
  ) => void;
}) {
  const [valueBasis, setValueBasis] = useState<CalculatorBasis>('ktc');
  const [searchQuery, setSearchQuery] = useState('');
  const [teamAReceives, setTeamAReceives] = useState<CalculatorAsset[]>([]);
  const [teamBReceives, setTeamBReceives] = useState<CalculatorAsset[]>([]);
  const [mySide, setMySide] = useState<CalculatorSide>('team-a');
  const [pickSide, setPickSide] = useState<CalculatorSide>('team-a');
  const [pickSeason, setPickSeason] = useState('2027');
  const [pickRound, setPickRound] = useState(1);
  const [pickSlot, setPickSlot] = useState('6');
  const [totalRosters, setTotalRosters] = useState(12);
  const [numQbs, setNumQbs] = useState(2);
  const [ppr, setPpr] = useState(1);
  const [waiverValue, setWaiverValue] = useState(250);
  const [addingPick, setAddingPick] = useState(false);

  const playerSearch = useBulkTradePlayerSearch(
    searchQuery,
  );

  const addAssetToSide = (
    side: CalculatorSide,
    asset: CalculatorAsset,
  ) => {
    const setter = side === 'team-a'
      ? setTeamAReceives
      : setTeamBReceives;

    setter((current) => [
      ...current,
      {
        ...asset,
        id: `${asset.id}-${current.length + 1}`,
      },
    ]);
  };

  const removeAsset = (
    side: CalculatorSide,
    assetId: string,
  ) => {
    const setter = side === 'team-a'
      ? setTeamAReceives
      : setTeamBReceives;

    setter((current) => current.filter(
      (asset) => asset.id !== assetId,
    ));
  };

  const teamATotal = useMemo(
    () => teamAReceives.reduce(
      (sum, asset) => sum + getAssetValue(asset, valueBasis),
      0,
    ),
    [teamAReceives, valueBasis],
  );
  const teamBTotal = useMemo(
    () => teamBReceives.reduce(
      (sum, asset) => sum + getAssetValue(asset, valueBasis),
      0,
    ),
    [teamBReceives, valueBasis],
  );

  const rosterSpotAdjustmentA = (
    teamBReceives.length - teamAReceives.length
  ) * waiverValue;
  const rosterSpotAdjustmentB = (
    teamAReceives.length - teamBReceives.length
  ) * waiverValue;
  const teamANet = teamATotal + rosterSpotAdjustmentA;
  const teamBNet = teamBTotal + rosterSpotAdjustmentB;
  const bulkOfferSeed = useMemo(
    () => buildBulkOfferSeed({
      mySide,
      teamAReceives,
      teamBReceives,
    }),
    [
      mySide,
      teamAReceives,
      teamBReceives,
    ],
  );

  const addPick = async () => {
    setAddingPick(true);

    try {
      const parsedSlot = pickSlot.trim()
        ? Number(pickSlot)
        : null;
      const pickValue = await fetchTradeCalculatorPickValue(
        pickSeason,
        pickRound,
        Number.isFinite(parsedSlot)
          ? parsedSlot
          : null,
        totalRosters,
        numQbs,
        ppr,
      );

      addAssetToSide(
        pickSide,
        {
          id: `pick-${pickSeason}-${pickRound}-${pickValue.slot ?? 'generic'}`,
          type: 'pick',
          label: pickValue.slot !== null
            ? `${pickSeason} Pick ${pickRound}.${String(pickValue.slot).padStart(2, '0')}`
            : `${pickSeason} Round ${pickRound}`,
          meta: `${totalRosters} team · ${numQbs === 2 ? 'SF' : '1QB'} · ${ppr} PPR`,
          ktcValue: pickValue.ktc_value,
          fcValue: pickValue.fc_value,
          pickSeason,
          pickRound,
        },
      );
    } catch {
      notify.error('Unable to load pick value.');
    } finally {
      setAddingPick(false);
    }
  };

  return (
    <div className="trades-container">
      <section className="trade-calculator-shell">
        <div className="trades-section-header">
          <div>
            <p className="page-eyebrow">Calculator</p>
            <h2 className="trades-section-title">Manual trade calculator</h2>
          </div>
        </div>

        <div className="trade-calculator-controls">
          <label>
            <span>Value basis</span>
            <select
              value={valueBasis}
              onChange={(event) => {
                setValueBasis(
                  event.target.value as CalculatorBasis,
                );
                setWaiverValue(
                  event.target.value === 'ktc'
                    ? 250
                    : 200,
                );
              }}
            >
              <option value="ktc">KTC</option>
              <option value="fantasycalc">FantasyCalc</option>
            </select>
          </label>

          <label>
            <span>Waiver spot value</span>
            <input
              type="number"
              value={waiverValue}
              onChange={(event) => {
                setWaiverValue(Number(event.target.value));
              }}
            />
          </label>

          <label>
            <span>Total rosters</span>
            <input
              type="number"
              min="8"
              max="32"
              value={totalRosters}
              onChange={(event) => {
                setTotalRosters(Number(event.target.value));
              }}
            />
          </label>

          <label>
            <span>QB format</span>
            <select
              value={numQbs}
              onChange={(event) => {
                setNumQbs(Number(event.target.value));
              }}
            >
              <option value={2}>Superflex</option>
              <option value={1}>1QB</option>
            </select>
          </label>

          <label>
            <span>PPR</span>
            <select
              value={ppr}
              onChange={(event) => {
                setPpr(Number(event.target.value));
              }}
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
              <option value={2}>2</option>
            </select>
          </label>

          <label>
            <span>My side</span>
            <select
              value={mySide}
              onChange={(event) => {
                setMySide(
                  event.target.value as CalculatorSide,
                );
              }}
            >
              <option value="team-a">Team A</option>
              <option value="team-b">Team B</option>
            </select>
          </label>
        </div>

        <div className="trade-calculator-builder">
          <label className="bulk-trade-search-label">
            <span>Add players</span>
            <div className="bulk-trade-search-input-wrap">
              <input
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                }}
                placeholder="Search player name"
              />
            </div>
          </label>

          {
            searchQuery.trim().length >= 2
              ? (
                <div className="bulk-trade-search-results">
                  {
                    playerSearch.data.map((player) => (
                      <div
                        key={player.player_id}
                        className="trade-calculator-search-row"
                      >
                        <div className="player-with-avatar">
                          <PlayerAvatar
                            playerId={player.player_id}
                            name={player.name}
                            size="sm"
                          />

                          <div className="player-with-avatar-copy">
                            <strong>{player.name}</strong>
                            <span>
                              {[player.position, player.team].filter(Boolean).join(' · ')}
                            </span>
                          </div>
                        </div>

                        <div className="trade-calculator-search-actions">
                          <span>
                            {valueBasis === 'ktc'
                              ? formatCalculatorValue(player.ktc_value ?? 0)
                              : formatCalculatorValue(player.fc_value ?? 0)}
                          </span>

                          <button
                            type="button"
                            className="button-secondary"
                            onClick={() => {
                              addAssetToSide(
                                'team-a',
                                buildPlayerAsset(player),
                              );
                            }}
                          >
                            Add to A
                          </button>

                          <button
                            type="button"
                            className="button-secondary"
                            onClick={() => {
                              addAssetToSide(
                                'team-b',
                                buildPlayerAsset(player),
                              );
                            }}
                          >
                            Add to B
                          </button>
                        </div>
                      </div>
                    ))
                  }

                  {
                    !playerSearch.loading
                    && playerSearch.data.length === 0
                      ? (
                        <div className="bulk-trade-empty-search">
                          No players found.
                        </div>
                      )
                      : null
                  }
                </div>
              )
              : null
          }

          <div className="trade-calculator-pick-builder">
            <label>
              <span>Add future pick</span>
              <select
                value={pickSide}
                onChange={(event) => {
                  setPickSide(
                    event.target.value as CalculatorSide,
                  );
                }}
              >
                <option value="team-a">Team A receives</option>
                <option value="team-b">Team B receives</option>
              </select>
            </label>

            <label>
              <span>Season</span>
              <input
                value={pickSeason}
                onChange={(event) => {
                  setPickSeason(event.target.value);
                }}
              />
            </label>

            <label>
              <span>Round</span>
              <input
                type="number"
                min="1"
                max="10"
                value={pickRound}
                onChange={(event) => {
                  setPickRound(Number(event.target.value));
                }}
              />
            </label>

            <label>
              <span>Slot</span>
              <input
                type="number"
                min="1"
                max="32"
                value={pickSlot}
                onChange={(event) => {
                  setPickSlot(event.target.value);
                }}
                placeholder="Optional"
              />
            </label>

            <button
              type="button"
              className="button-primary"
              onClick={() => {
                void addPick();
              }}
              disabled={addingPick}
            >
              {addingPick ? 'Adding...' : 'Add pick'}
            </button>
          </div>
        </div>

        <div className="trade-calculator-grid">
          {
            [
              {
                side: 'team-a' as const,
                title: 'Team A receives',
                assets: teamAReceives,
                total: teamATotal,
                adjustment: rosterSpotAdjustmentA,
                net: teamANet,
              },
              {
                side: 'team-b' as const,
                title: 'Team B receives',
                assets: teamBReceives,
                total: teamBTotal,
                adjustment: rosterSpotAdjustmentB,
                net: teamBNet,
              },
            ].map((panel) => (
              <section
                key={panel.side}
                className="trade-calculator-panel"
              >
                <div className="trade-calculator-panel-header">
                  <h3>{panel.title}</h3>
                  <strong>{formatCalculatorValue(panel.net)}</strong>
                </div>

                <div className="trade-calculator-asset-list">
                  {
                    panel.assets.length > 0
                      ? panel.assets.map((asset) => (
                          <div
                            key={asset.id}
                            className="trade-calculator-asset-row"
                          >
                            <div>
                              <strong>{asset.label}</strong>
                              <span>{asset.meta}</span>
                            </div>

                            <div className="trade-calculator-asset-actions">
                              <span>
                                {
                                  formatCalculatorValue(
                                    getAssetValue(asset, valueBasis),
                                  )
                                }
                              </span>
                              <button
                                type="button"
                                className="button-secondary"
                                onClick={() => {
                                  removeAsset(
                                    panel.side,
                                    asset.id,
                                  );
                                }}
                              >
                                Remove
                              </button>
                            </div>
                          </div>
                        ))
                      : (
                        <div className="commissioner-empty-note">
                          No assets added yet.
                        </div>
                      )
                  }
                </div>

                <div className="trade-calculator-summary">
                  <div>
                    <span>Asset total</span>
                    <strong>{formatCalculatorValue(panel.total)}</strong>
                  </div>
                  <div>
                    <span>Roster spots</span>
                    <strong>{formatCalculatorValue(panel.adjustment)}</strong>
                  </div>
                </div>
              </section>
            ))
          }
        </div>

        <div className="trade-calculator-bulk-send">
          <div>
            <span className="page-eyebrow">Bulk send</span>
            <p>
              Seed the Bulk Offers tab when one side is all players and the other side is all picks.
            </p>
          </div>

          <button
            type="button"
            className="button-primary"
            disabled={!bulkOfferSeed}
            onClick={() => {
              if (!bulkOfferSeed || !onSendToBulkOffers) {
                return;
              }

              onSendToBulkOffers(
                bulkOfferSeed,
              );
            }}
          >
            Send to bulk offers
          </button>
        </div>
      </section>
    </div>
  );
}
