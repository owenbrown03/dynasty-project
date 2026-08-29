import { Fragment, useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  ArrowLeftRight,
  Calculator,
  Flame,
  MoreHorizontal,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import { useNavigate } from 'react-router';

import './PlayerTable.css';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { useToggleTradeBlock } from '@/hooks/sleeper/useTrades';
import { useSubmitWaiverClaim } from '@/hooks/sleeper/useWaivers';
import { notify } from '@/utils/notify';
import type {
  BulkTradePlayerSearchResult,
  LeaguePlayer,
  ValueBasis,
  WarValueSettings,
} from '@/types';
import { formatNumber } from '@/utils/format';
import { getPositionColor } from '@/utils/positions';
import {
  getLeaguePlayerSelectedValue,
  getValueBasisLabel,
} from '@/utils/valueBasis';

interface SlotSegment {
  letter: string;
  position?: string;
}

function getSlotSegments(slot: string | null | undefined): SlotSegment[] {
  if (!slot) {
    return [{ letter: '-' }];
  }

  switch (slot) {
    case 'FLEX':
    case 'WRTB_FLEX':
      return [
        { letter: 'W', position: 'WR' },
        { letter: 'R', position: 'RB' },
        { letter: 'T', position: 'TE' },
      ];
    case 'SUPER_FLEX':
    case 'SF':
    case 'OP':
      return [
        { letter: 'W', position: 'WR' },
        { letter: 'R', position: 'RB' },
        { letter: 'T', position: 'TE' },
        { letter: 'Q', position: 'QB' },
      ];
    case 'WRRB_FLEX':
      return [
        { letter: 'W', position: 'WR' },
        { letter: 'R', position: 'RB' },
      ];
    case 'REC_FLEX':
      return [
        { letter: 'W', position: 'WR' },
        { letter: 'T', position: 'TE' },
      ];
    case 'IDP_FLEX':
      return [
        { letter: 'I', position: 'IDP' },
        { letter: 'D', position: 'IDP' },
        { letter: 'P', position: 'IDP' },
      ];
    case 'QB':
      return [{ letter: 'QB', position: 'QB' }];
    case 'RB':
      return [{ letter: 'RB', position: 'RB' }];
    case 'WR':
      return [{ letter: 'WR', position: 'WR' }];
    case 'TE':
      return [{ letter: 'TE', position: 'TE' }];
    case 'BN':
      return [{ letter: 'BN' }];
    default:
      return [{ letter: slot, position: slot }];
  }
}

function SlotDisplay({
  slot,
  empty = false,
}: {
  slot: string | null | undefined;
  empty?: boolean;
}) {
  const segments = getSlotSegments(slot);

  return (
    <span
      className={
        empty
          ? 'player-table-slot-text player-table-slot-text-empty'
          : 'player-table-slot-text'
      }
    >
      {segments.map((seg, i) => (
        <span
          key={i}
          style={{
            color: empty
              ? undefined
              : seg.position
                ? getPositionColor(seg.position)
                : 'var(--color-text-muted)',
          }}
        >
          {seg.letter}
        </span>
      ))}
    </span>
  );
}

function getCompactValueBasisMeta(valueBasis: ValueBasis): { label: string; tooltip: string } {
  switch (valueBasis) {
    case 'dynasty_roster_war':
      return { label: 'D-WAR', tooltip: 'Dynasty Roster WAR' };
    case 'dynasty_starter_war':
      return { label: 'D-WAR', tooltip: 'Dynasty Starter WAR' };
    case 'my_roster_war':
      return { label: 'D-WAR', tooltip: 'Dynasty Roster WAR (My Model)' };
    case 'my_starter_war':
      return { label: 'D-WAR', tooltip: 'Dynasty Starter WAR (My Model)' };
    case 'redraft_roster_war':
      return { label: 'R-WAR', tooltip: 'Redraft Roster WAR' };
    case 'redraft_starter_war':
      return { label: 'R-WAR', tooltip: 'Redraft Starter WAR' };
    case 'sleeper_war':
      return { label: 'S-WAR', tooltip: 'Sleeper WAR' };
    case 'my_war':
      return { label: 'My WAR', tooltip: 'My Custom WAR' };
    case 'fantasycalc':
      return { label: 'FC', tooltip: 'FantasyCalc Dynasty Value' };
    case 'fantasycalc_redraft':
      return { label: 'FC (R)', tooltip: 'FantasyCalc Redraft Value' };
    case 'ktc':
      return { label: 'KTC', tooltip: 'KeepTradeCut Dynasty Value' };
    case 'ktc_redraft':
      return { label: 'KTC (R)', tooltip: 'KeepTradeCut Redraft Value' };
    case 'adp':
      return { label: 'ADP', tooltip: 'Average Draft Position' };
    case 'sleeper_projection':
      return { label: 'Proj', tooltip: 'Sleeper Projected Points' };
    default:
      return {
        label: getValueBasisLabel(valueBasis),
        tooltip: getValueBasisLabel(valueBasis),
      };
  }
}

interface Props {
  players: LeaguePlayer[];
  emptyStarterSlots?: string[] | null;
  valueBasis: ValueBasis;
  redraftValueBasis?: ValueBasis;
  warValueSettings: WarValueSettings;
  leagueId?: string;
  rosterId?: number;
  isUserRoster?: boolean;
}

export function PlayerTable({
  players,
  emptyStarterSlots,
  valueBasis,
  redraftValueBasis,
  warValueSettings,
  leagueId,
  rosterId,
  isUserRoster = false,
}: Props) {
  const navigate = useNavigate();
  const toggleTradeBlock = useToggleTradeBlock();
  const submitClaim = useSubmitWaiverClaim();

  const [activeMenuPlayerId, setActiveMenuPlayerId] = useState<string | null>(null);
  const [playerToCut, setPlayerToCut] = useState<LeaguePlayer | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const valueMeta = getCompactValueBasisMeta(valueBasis);
  const redraftMeta = redraftValueBasis
    ? getCompactValueBasisMeta(redraftValueBasis)
    : null;

  const firstBenchIndex = players.findIndex(
    (player) => !player.is_starter,
  );

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setActiveMenuPlayerId(null);
      }
    }
    if (activeMenuPlayerId) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [activeMenuPlayerId]);

  const toPlayerAsset = (player: LeaguePlayer): BulkTradePlayerSearchResult => ({
    player_id: player.player_id,
    name: player.name,
    position: player.position,
    team: player.team,
    age: player.age,
    ktc_value: player.ktc_value,
    fc_value: player.fc_value,
    underdog_position_rank: player.underdog_position_rank,
  });

  const handleTradePlayer = (player: LeaguePlayer) => {
    const playerAsset = toPlayerAsset(player);
    navigate('/trades', {
      state: {
        seed: isUserRoster
          ? {
              sendPlayers: [playerAsset],
              sendPicks: [],
              receivePlayers: [],
              receivePicks: [],
              preferredLeagueId: leagueId,
            }
          : {
              sendPlayers: [],
              sendPicks: [],
              receivePlayers: [playerAsset],
              receivePicks: [],
              preferredLeagueId: leagueId,
            },
      },
    });
  };

  const handleToggleBlock = (player: LeaguePlayer) => {
    if (!leagueId) return;
    toggleTradeBlock.mutate({
      league_id: leagueId,
      player_id: player.player_id,
    });
  };

  const handleConfirmCut = async () => {
    if (!playerToCut || !leagueId || !rosterId) return;
    try {
      await submitClaim.submitClaimAsync({
        league_id: leagueId,
        roster_id: rosterId,
        drop_player_id: playerToCut.player_id,
        bid: 0,
      });
      notify.success(`Successfully dropped ${playerToCut.name}`);
      setPlayerToCut(null);
      setActiveMenuPlayerId(null);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      notify.error(error?.response?.data?.detail || error?.message || 'Failed to drop player');
    }
  };

  return (
    <div className="player-table-scroll">
      <table className="player-table">
        <thead>
          <tr>
            <th className="player-table-slot-col">Slot</th>
            <th className="player-table-name-col">Name</th>
            <th className="player-table-pos-col">Pos</th>
            <th className="player-table-team-col">Team</th>
            <th className="player-table-num-col" title="Projected Points">Proj</th>
            <th className="player-table-ud-col" title="Underdog Position Rank">UD</th>
            <th className="player-table-num-col" title={valueMeta.tooltip}>{valueMeta.label}</th>
            {redraftMeta ? (
              <th className="player-table-num-col" title={redraftMeta.tooltip}>
                {redraftMeta.label}
              </th>
            ) : null}
            <th className="player-table-actions-col">Actions</th>
          </tr>
        </thead>

        <tbody>
          {players.map((player, index) => (
            <Fragment key={player.player_id}>
              {index === firstBenchIndex
                && firstBenchIndex > 0
                && (emptyStarterSlots ?? []).length > 0
                && (emptyStarterSlots ?? []).map((slot) => (
                  <tr
                    key={`empty-${slot}`}
                    className="player-table-row-empty"
                  >
                    <td className="player-table-slot-cell">
                      <SlotDisplay slot={slot} empty />
                    </td>
                    <td
                      colSpan={redraftMeta ? 8 : 7}
                      className="player-table-empty-label"
                    >
                      Empty Starter Slot
                    </td>
                  </tr>
                ))}

              {index === firstBenchIndex ? (
                <tr className="player-table-divider">
                  <td colSpan={redraftMeta ? 9 : 8}>
                    <div className="player-table-divider-inner">
                      <span>Bench</span>
                    </div>
                  </td>
                </tr>
              ) : null}

              <tr
                className={
                  player.is_starter
                    ? 'player-table-row-starter'
                    : 'player-table-row-bench'
                }
              >
                <td className="player-table-slot-cell">
                  <SlotDisplay
                    slot={player.slot ?? (player.is_starter ? 'STARTER' : 'BN')}
                  />
                </td>

                <td className="player-table-name-cell">
                  <div className="player-with-avatar">
                    <PlayerAvatar
                      playerId={player.player_id}
                      name={player.name}
                      size="sm"
                    />
                    <span className="player-table-name">
                      {player.name}
                    </span>
                    {player.on_block ? (
                      <span className="player-table-otb-pill" title="On Sleeper Trade Block">
                        OTB
                      </span>
                    ) : null}
                  </div>
                </td>

                <td
                  className="player-table-position-cell"
                  style={{
                    color: getPositionColor(player.position),
                  }}
                >
                  {player.position}
                </td>

                <td className="player-table-team-cell">
                  {player.team ?? 'FA'}
                </td>

                <td className="player-table-num-cell">
                  {formatNumber(player.projected_points)}
                </td>

                <td className="player-table-ud-cell">
                  {player.underdog_position_rank ? (
                    player.position && player.underdog_position_rank.toUpperCase().startsWith(player.position.toUpperCase())
                      ? player.underdog_position_rank
                      : `${player.position ?? ''}${player.underdog_position_rank}`
                  ) : '—'}
                </td>

                <td className="player-table-num-cell">
                  {
                    formatNumber(
                      getLeaguePlayerSelectedValue(
                        player,
                        valueBasis,
                        warValueSettings,
                      ),
                      (
                        valueBasis === 'ktc'
                        || valueBasis === 'fantasycalc'
                        || valueBasis === 'adp'
                      )
                        ? 0
                        : 2,
                    )
                  }
                </td>

                {redraftMeta ? (
                  <td className="player-table-num-cell">
                    {
                      formatNumber(
                        getLeaguePlayerSelectedValue(
                          player,
                          redraftValueBasis ?? 'ktc',
                          warValueSettings,
                        ),
                        (
                          redraftValueBasis === 'ktc'
                          || redraftValueBasis === 'fantasycalc'
                          || redraftValueBasis === 'adp'
                        )
                          ? 0
                          : 2,
                      )
                    }
                  </td>
                ) : null}

                <td className="player-table-actions-cell">
                  <div className="player-table-actions">
                    <button
                      type="button"
                      className="player-table-btn player-table-btn-trade"
                      title={isUserRoster ? `Offer ${player.name} in a trade` : `Trade for ${player.name}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTradePlayer(player);
                      }}
                    >
                      <ArrowLeftRight size={11} />
                      <span>Trade</span>
                    </button>

                    {isUserRoster && leagueId ? (
                      <button
                        type="button"
                        className={`player-table-btn player-table-btn-block ${player.on_block ? 'active' : ''}`}
                        title={player.on_block ? 'On Sleeper Trade Block — click to remove' : 'Put on Sleeper Trade Block'}
                        disabled={toggleTradeBlock.isPending}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleBlock(player);
                        }}
                      >
                        <Flame size={11} />
                        <span>{player.on_block ? 'On Block' : '+ Block'}</span>
                      </button>
                    ) : null}

                    <div className="player-table-menu-container">
                      <button
                        type="button"
                        className={`player-table-btn player-table-btn-more ${activeMenuPlayerId === player.player_id ? 'active' : ''}`}
                        title="Player options"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveMenuPlayerId(
                            activeMenuPlayerId === player.player_id ? null : player.player_id,
                          );
                        }}
                      >
                        <MoreHorizontal size={13} />
                      </button>

                      {activeMenuPlayerId === player.player_id && (
                        <div
                          ref={menuRef}
                          className="player-table-dropdown-menu"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="player-table-dropdown-header">
                            <strong>{player.name}</strong>
                            <small>{player.position} · {player.team ?? 'FA'}</small>
                          </div>

                          <button
                            type="button"
                            className="player-table-dropdown-item"
                            onClick={() => {
                              setActiveMenuPlayerId(null);
                              handleTradePlayer(player);
                            }}
                          >
                            <ArrowLeftRight size={13} />
                            <span>{isUserRoster ? 'Create Bulk Offer' : 'Trade for Player'}</span>
                          </button>

                          <button
                            type="button"
                            className="player-table-dropdown-item"
                            onClick={() => {
                              setActiveMenuPlayerId(null);
                              handleTradePlayer(player);
                            }}
                          >
                            <Calculator size={13} />
                            <span>Trade Calculator</span>
                          </button>

                          {isUserRoster && leagueId ? (
                            <button
                              type="button"
                              className="player-table-dropdown-item"
                              disabled={toggleTradeBlock.isPending}
                              onClick={() => {
                                setActiveMenuPlayerId(null);
                                handleToggleBlock(player);
                              }}
                            >
                              <Flame size={13} />
                              <span>{player.on_block ? 'Remove from Trade Block' : 'Put on Trade Block'}</span>
                            </button>
                          ) : null}

                          {leagueId ? (
                            <button
                              type="button"
                              className="player-table-dropdown-item"
                              onClick={() => {
                                setActiveMenuPlayerId(null);
                                navigate('/waivers');
                              }}
                            >
                              <Search size={13} />
                              <span>Browse Waivers</span>
                            </button>
                          ) : null}

                          {isUserRoster && leagueId && rosterId ? (
                            <button
                              type="button"
                              className="player-table-dropdown-item player-table-dropdown-danger"
                              onClick={() => {
                                setActiveMenuPlayerId(null);
                                setPlayerToCut(player);
                              }}
                            >
                              <Trash2 size={13} />
                              <span>Drop Player</span>
                            </button>
                          ) : null}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
              </tr>
            </Fragment>
          ))}
        </tbody>
      </table>

      {playerToCut ? (
        <div className="player-cut-backdrop" onClick={() => setPlayerToCut(null)}>
          <div className="player-cut-modal" onClick={(e) => e.stopPropagation()}>
            <div className="player-cut-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={18} color="#ef4444" />
                <h3>Drop Player</h3>
              </div>
              <button
                type="button"
                className="player-cut-close"
                onClick={() => setPlayerToCut(null)}
              >
                <X size={16} />
              </button>
            </div>

            <div className="player-cut-modal-body">
              <p style={{ margin: '0 0 12px 0' }}>
                Are you sure you want to drop <strong>{playerToCut.name}</strong> ({playerToCut.position} - {playerToCut.team ?? 'FA'}) from your roster?
              </p>
              <div className="player-cut-warning">
                ⚠️ This will submit an immediate drop transaction to Sleeper and release this player to waivers.
              </div>
            </div>

            <div className="player-cut-modal-actions">
              <button
                type="button"
                className="player-cut-btn-cancel"
                onClick={() => setPlayerToCut(null)}
                disabled={submitClaim.submitting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="player-cut-btn-confirm"
                onClick={() => void handleConfirmCut()}
                disabled={submitClaim.submitting}
              >
                {submitClaim.submitting ? 'Dropping...' : 'Drop Player'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
