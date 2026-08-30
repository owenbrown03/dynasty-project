import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import { api } from '@/api/v1/endpoints';
import { useValuePreference } from '@/context/useValuePreference';
import {
  fetchTradeCalculatorPickValue,
} from '@/hooks/sleeper/useBulkTrades';
import type {
  BulkTradePlayerSearchResult,
  BulkTradePickRequest,
  ValueBasis,
} from '@/types';
import { notify } from '@/utils/notify';
import { TradeSideCard, type TradeSideAsset } from '@/components/trades/TradeSideCard';
import { TradeWinningBar } from '@/components/trades/TradeWinningBar';
import './TradeCalculatorTab.css';


export type CalculatorBasis =
  | 'ktc'
  | 'fantasycalc'
  | 'dynasty_starter_war'
  | 'dynasty_roster_war'
  | 'redraft_starter_war'
  | 'redraft_roster_war'
  | 'my_war';

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
  rookieWarValue?: number | null;
  player?: BulkTradePlayerSearchResult;
  pickSeason?: string;
  pickRound?: number;
};

export interface TradeCalculatorBulkOfferSeed {
  sendPlayers: BulkTradePlayerSearchResult[];
  sendPicks: BulkTradePickRequest[];
  receivePlayers: BulkTradePlayerSearchResult[];
  receivePicks: BulkTradePickRequest[];
}


function getAssetValue(
  asset: CalculatorAsset,
  basis: CalculatorBasis,
) {
  if (asset.type === 'pick') {
    if (basis === 'fantasycalc') {
      return asset.fcValue ?? 0;
    }
    if (basis.includes('war')) {
      return asset.rookieWarValue ?? 0;
    }
    return asset.ktcValue ?? 0;
  }

  const p = asset.player;
  if (!p) {
    if (basis === 'fantasycalc') {
      return asset.fcValue ?? 0;
    }
    return asset.ktcValue ?? 0;
  }

  switch (basis) {
    case 'ktc':
      return p.ktc_value ?? 0;
    case 'fantasycalc':
      return p.fc_value ?? 0;
    case 'dynasty_starter_war':
      return p.dynasty_starter_war ?? 0;
    case 'dynasty_roster_war':
      return p.dynasty_roster_war ?? 0;
    case 'redraft_starter_war':
      return p.redraft_starter_war ?? 0;
    case 'redraft_roster_war':
      return p.redraft_roster_war ?? 0;
    case 'my_war':
      return p.my_dynasty_starter_war ?? p.dynasty_starter_war ?? 0;
    default:
      return p.ktc_value ?? 0;
  }
}


function buildPlayerAsset(
  player: BulkTradePlayerSearchResult,
): CalculatorAsset {
  return {
    id: `player-${player.player_id}`,
    type: 'player' as const,
    label: player.name,
    meta: [
      player.position,
      player.team,
      player.age !== null
        ? `${player.age} y.o.`
        : null,
    ]
      .filter(Boolean)
      .join(' · '),
    ktcValue: player.ktc_value,
    fcValue: player.fc_value,
    player,
  };
}

function toTradeSideAssets(
  assets: CalculatorAsset[],
  basis: CalculatorBasis,
): TradeSideAsset[] {
  return assets.map((a) => ({
    id: a.id,
    type: a.type,
    label: a.label,
    meta: a.meta,
    value: getAssetValue(a, basis),
    position: a.player?.position ?? (a.type === 'pick' ? 'PICK' : null),
    team: a.player?.team ?? null,
    age: a.player?.age ?? null,
    playerId: a.player?.player_id ?? null,
    underdogRank: a.player?.underdog_position_rank ?? null,
  }));
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
    myAssets.length === 0
    || counterpartyAssets.length === 0
  ) {
    return null;
  }

  return {
    sendPlayers: myPlayers.map(
      asset => asset.player!,
    ),
    sendPicks: myPicks.map(
      asset => ({
        season: asset.pickSeason!,
        round: asset.pickRound!,
      }),
    ),
    receivePlayers: counterpartyPlayers.map(
      asset => asset.player!,
    ),
    receivePicks: counterpartyPicks.map(
      asset => ({
        season: asset.pickSeason!,
        round: asset.pickRound!,
      }),
    ),
  };
}


interface TradeCalculatorTabProps {
  seed?: TradeCalculatorBulkOfferSeed | null;
  onSendToBulkOffers?: (
    seed: TradeCalculatorBulkOfferSeed,
  ) => void;
}

export function TradeCalculatorTab({
  seed,
  onSendToBulkOffers,
}: TradeCalculatorTabProps) {
  const { preference, setPreference } = useValuePreference();
  const [valueBasis, setValueBasis] = useState<CalculatorBasis>(
    preference === 'fantasycalc' ? 'fantasycalc' : 'ktc',
  );

  useEffect(() => {
    setValueBasis(preference === 'fantasycalc' ? 'fantasycalc' : 'ktc');
  }, [preference]);

  const [waiverValue, setWaiverValue] = useState(500);
  const [totalRosters, setTotalRosters] = useState(12);
  const [numQbs, setNumQbs] = useState(2);
  const [ppr, setPpr] = useState(1);
  const [mySide, setMySide] = useState<CalculatorSide>('team-a');

  const [teamAReceives, setTeamAReceives] = useState<CalculatorAsset[]>([]);
  const [teamBReceives, setTeamBReceives] = useState<CalculatorAsset[]>([]);

  const [waiverCredits, setWaiverCredits] = useState<{
    a: number;
    b: number;
  } | null>(null);

  // Apply seeds when passed
  useEffect(() => {
    if (!seed) {
      return;
    }

    let isMounted = true;

    const loadSeed = async () => {
      const resolvePick = async (pick: { season: string; round: number }, index: number, prefix: string) => {
        try {
          const value = await fetchTradeCalculatorPickValue(
            pick.season,
            pick.round,
            null,
            totalRosters,
            numQbs,
            ppr,
          );
          return {
            id: `seed-${prefix}-pick-${pick.season}-${pick.round}-${index}`,
            type: 'pick' as const,
            label: `${pick.season} Round ${pick.round}`,
            meta: `${totalRosters} tm · ${numQbs === 2 ? 'SF' : '1QB'} · ${ppr} PPR`,
            ktcValue: value.ktc_value,
            fcValue: value.fc_value,
            rookieWarValue: value.rookie_war_value,
            pickSeason: pick.season,
            pickRound: pick.round,
          };
        } catch {
          return {
            id: `seed-${prefix}-pick-${pick.season}-${pick.round}-${index}`,
            type: 'pick' as const,
            label: `${pick.season} Round ${pick.round}`,
            meta: 'Draft pick',
            ktcValue: 0,
            fcValue: 0,
            rookieWarValue: 0,
            pickSeason: pick.season,
            pickRound: pick.round,
          };
        }
      };

      const sendPicks = await Promise.all(
        seed.sendPicks.map((p, i) => resolvePick(p, i, 'send')),
      );
      const receivePicks = await Promise.all(
        seed.receivePicks.map((p, i) => resolvePick(p, i, 'receive')),
      );

      if (!isMounted) return;

      setTeamAReceives([
        ...seed.sendPlayers.map(buildPlayerAsset),
        ...sendPicks,
      ]);

      setTeamBReceives([
        ...seed.receivePlayers.map(buildPlayerAsset),
        ...receivePicks,
      ]);
    };

    void loadSeed();

    return () => {
      isMounted = false;
    };
  }, [seed]); // We do not depend on format controls here intentionally, so it doesn't reset user edits when changing format.

  // Query waiver ladder adjustments dynamically
  useEffect(() => {
    const aOut = teamBReceives.filter(
      (asset) => asset.type !== 'pick',
    ).length;
    const bOut = teamAReceives.filter(
      (asset) => asset.type !== 'pick',
    ).length;

    if (aOut === 0 && bOut === 0) {
      setWaiverCredits(null);
      return;
    }

    const controller = new AbortController();

    api.trades
      .getTradeCalculatorWaiverAdjustment(
        totalRosters,
        numQbs,
        ppr,
        aOut,
        bOut,
        controller.signal,
      )
      .then((response) => {
        setWaiverCredits({
          a: response.data.my_credit ?? 0,
          b: response.data.their_credit ?? 0,
        });
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setWaiverCredits(null);
        }
      });

    return () => controller.abort();
  }, [
    teamAReceives,
    teamBReceives,
    totalRosters,
    numQbs,
    ppr,
  ]);

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
        id: `${asset.id}-${current.length + 1}-${Date.now()}`,
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

  const handleAddPick = async (
    side: CalculatorSide,
    season: string,
    round: number,
    slot?: number | null,
  ) => {
    try {
      const pickValue = await fetchTradeCalculatorPickValue(
        season,
        round,
        slot ?? null,
        totalRosters,
        numQbs,
        ppr,
      );

      addAssetToSide(
        side,
        {
          id: `pick-${season}-${round}-${pickValue.slot ?? 'generic'}`,
          type: 'pick',
          label: pickValue.slot !== null
            ? `${season} Pick ${round}.${String(pickValue.slot).padStart(2, '0')}`
            : `${season} Round ${round}`,
          meta: `${totalRosters} tm · ${numQbs === 2 ? 'SF' : '1QB'} · ${ppr} PPR`,
          ktcValue: pickValue.ktc_value,
          fcValue: pickValue.fc_value,
          rookieWarValue: pickValue.rookie_war_value,
          pickSeason: season,
          pickRound: round,
        },
      );
    } catch {
      notify.error('Unable to load pick value.');
    }
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

  const flatAdjustmentA = (
    teamBReceives.length - teamAReceives.length
  ) * waiverValue;
  const flatAdjustmentB = (
    teamAReceives.length - teamBReceives.length
  ) * waiverValue;

  const rosterSpotAdjustmentA =
    waiverCredits?.a ?? flatAdjustmentA;
  const rosterSpotAdjustmentB =
    waiverCredits?.b ?? flatAdjustmentB;

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

  return (
    <div className="trades-container">
      <section className="trade-calculator-shell">
        <div className="trades-section-header">
          <div>
            <p className="page-eyebrow">Calculator</p>
            <h2 className="trades-section-title">Trade Calculator</h2>
          </div>
        </div>

        {/* League & Format Controls */}
        <div className="trade-calculator-controls">
          <label>
            <span>Value basis</span>
            <select
              value={valueBasis}
              onChange={(e) => {
                const next = e.target.value as CalculatorBasis;
                setValueBasis(next);
                void setPreference(next as ValueBasis);
              }}
            >
              <optgroup label="Market Values">
                <option value="ktc">KeepTradeCut (KTC)</option>
                <option value="fantasycalc">FantasyCalc (FC)</option>
              </optgroup>
              <optgroup label="WAR (Wins Above Replacement)">
                <option value="dynasty_starter_war">Dynasty WAR (Starters)</option>
                <option value="dynasty_roster_war">Dynasty WAR (Full Roster)</option>
                <option value="redraft_starter_war">Redraft WAR (Starters)</option>
                <option value="redraft_roster_war">Redraft WAR (Full Roster)</option>
                <option value="my_war">My Dynasty WAR</option>
              </optgroup>
            </select>
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
            <span>Waiver spot value</span>
            <input
              type="number"
              min="0"
              max="5000"
              value={waiverValue}
              onChange={(event) => {
                setWaiverValue(Number(event.target.value));
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
              <option value={2}>Superflex (2QB / SF)</option>
              <option value={1}>1QB</option>
            </select>
          </label>

          <label>
            <span>PPR Scoring</span>
            <select
              value={ppr}
              onChange={(event) => {
                setPpr(Number(event.target.value));
              }}
            >
              <option value={0}>Standard (0 PPR)</option>
              <option value={0.5}>Half PPR (0.5)</option>
              <option value={1}>Full PPR (1.0)</option>
              <option value={2}>2.0 PPR</option>
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
              <option value="team-a">Team 1 (Left)</option>
              <option value="team-b">Team 2 (Right)</option>
            </select>
          </label>
        </div>

        {/* Side-by-Side KTC-Style Trade Builder */}
        <div className="trade-calculator-two-column-grid">
          <TradeSideCard
            title="Team 1 gets..."
            side="team-a"
            assets={toTradeSideAssets(teamAReceives, valueBasis)}
            totalValue={teamATotal}
            adjustmentValue={rosterSpotAdjustmentA}
            adjustmentLabel="Value Adjustment"
            netValue={teamANet}
            onAddPlayer={(player) => addAssetToSide('team-a', buildPlayerAsset(player))}
            onAddPick={(season, round, slot) => handleAddPick('team-a', season, round, slot)}
            onRemoveAsset={(assetId) => removeAsset('team-a', assetId)}
            valueBasis={valueBasis}
            searchPlaceholder="Search for a player to add to Team 1..."
          />

          <TradeSideCard
            title="Team 2 gets..."
            side="team-b"
            assets={toTradeSideAssets(teamBReceives, valueBasis)}
            totalValue={teamBTotal}
            adjustmentValue={rosterSpotAdjustmentB}
            adjustmentLabel="Value Adjustment"
            netValue={teamBNet}
            onAddPlayer={(player) => addAssetToSide('team-b', buildPlayerAsset(player))}
            onAddPick={(season, round, slot) => handleAddPick('team-b', season, round, slot)}
            onRemoveAsset={(assetId) => removeAsset('team-b', assetId)}
            valueBasis={valueBasis}
            searchPlaceholder="Search for a player to add to Team 2..."
          />
        </div>

        {/* Visual Winning Meter & Advice Bar */}
        <TradeWinningBar
          teamAName="Team 1"
          teamBName="Team 2"
          teamANet={teamANet}
          teamBNet={teamBNet}
          valueBasis={valueBasis}
        />

        {/* Bulk Send Integration Footer */}
        <div className="trade-calculator-bulk-send">
          <div>
            <span className="page-eyebrow">Bulk Send</span>
            <p>
              Seed the Bulk Offers tab with this trade package across your eligible leagues.
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
            Send to Bulk Offers
          </button>
        </div>
      </section>
    </div>
  );
}
