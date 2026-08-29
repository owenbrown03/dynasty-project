import { useState, useRef, useEffect, useMemo } from 'react';
import { Search, X, Plus, Calendar } from 'lucide-react';
import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import { TeamBadge } from '@/components/players/TeamBadge';
import { Skeleton } from '@/components/feedback/Skeleton';
import { useBulkTradePlayerSearch } from '@/hooks/sleeper/useBulkTrades';
import type { BulkTradePlayerSearchResult } from '@/types';
import { formatMarketValue } from '@/utils/valueFormat';
import { getPositionColor } from '@/utils/positions';
import './TradeSideCard.css';

export interface TradeSideAsset {
  id: string;
  type: 'player' | 'pick';
  label: string;
  meta: string;
  value: number;
  position?: string | null;
  team?: string | null;
  age?: number | null;
  playerId?: string | null;
  underdogRank?: string | null;
}

export interface TradeSideCardProps {
  title: string;
  side: 'team-a' | 'team-b';
  assets: TradeSideAsset[];
  totalValue: number;
  adjustmentValue?: number;
  adjustmentLabel?: string;
  netValue: number;
  onAddPlayer: (player: BulkTradePlayerSearchResult) => void;
  onAddPick?: (season: string, round: number, slot?: number | null) => void;
  onRemoveAsset: (assetId: string) => void;
  valueBasis?: 'ktc' | 'fantasycalc';
  searchPlaceholder?: string;
  validPickYears?: string[];
}

export function TradeSideCard({
  title,
  assets,
  totalValue,
  adjustmentValue = 0,
  adjustmentLabel = 'Value Adjustment',
  netValue,
  onAddPlayer,
  onAddPick,
  onRemoveAsset,
  valueBasis = 'ktc',
  searchPlaceholder = 'Search for a player or pick...',
  validPickYears = ['2025', '2026', '2027'],
}: TradeSideCardProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [activeSearchTab, setActiveSearchTab] = useState<'players' | 'picks'>('players');
  const [customPickSeason, setCustomPickSeason] = useState(validPickYears[0] ?? '2026');
  const [customPickRound, setCustomPickRound] = useState(1);
  const [customPickSlot, setCustomPickSlot] = useState('');

  const containerRef = useRef<HTMLDivElement>(null);
  const playerSearch = useBulkTradePlayerSearch(searchQuery);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Compute piece summary counts
  const pieceSummary = useMemo(() => {
    const counts: Record<string, number> = {};
    let pickCount = 0;

    for (const asset of assets) {
      if (asset.type === 'pick') {
        pickCount += 1;
      } else if (asset.position) {
        counts[asset.position] = (counts[asset.position] ?? 0) + 1;
      }
    }

    const parts: string[] = [];
    for (const [pos, count] of Object.entries(counts)) {
      parts.push(`${count} ${pos}`);
    }
    if (pickCount > 0) {
      parts.push(`${pickCount} ${pickCount === 1 ? 'Pick' : 'Picks'}`);
    }

    return parts.join(', ') || 'No pieces';
  }, [assets]);

  const handleSelectPlayer = (player: BulkTradePlayerSearchResult) => {
    onAddPlayer(player);
    setSearchQuery('');
    setIsDropdownOpen(false);
  };

  const handleSelectQuickPick = (season: string, round: number) => {
    if (onAddPick) {
      onAddPick(season, round);
    }
    setIsDropdownOpen(false);
  };

  const handleAddCustomPick = () => {
    if (onAddPick) {
      const slotNum = customPickSlot.trim() ? Number(customPickSlot) : null;
      onAddPick(customPickSeason, customPickRound, Number.isFinite(slotNum) ? slotNum : null);
    }
    setIsDropdownOpen(false);
  };

  return (
    <div className="trade-side-card" ref={containerRef}>
      {/* Header bar */}
      <div className="trade-side-header">
        <h3 className="trade-side-title">{title}</h3>
      </div>

      {/* Integrated Search Box */}
      <div className="trade-side-search-section">
        <div className="trade-side-search-input-wrap">
          <Search size={15} className="trade-side-search-icon" />
          <input
            type="text"
            className="trade-side-search-input"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setIsDropdownOpen(true);
            }}
            onFocus={() => setIsDropdownOpen(true)}
          />
          {searchQuery ? (
            <button
              type="button"
              className="trade-side-search-clear"
              onClick={() => {
                setSearchQuery('');
              }}
              title="Clear search"
            >
              <X size={14} />
            </button>
          ) : null}
        </div>

        {/* Dropdown Menu */}
        {isDropdownOpen ? (
          <div className="trade-side-dropdown">
            {onAddPick ? (
              <div className="trade-side-dropdown-tabs">
                <button
                  type="button"
                  className={`trade-side-dropdown-tab ${activeSearchTab === 'players' ? 'active' : ''}`}
                  onClick={() => setActiveSearchTab('players')}
                >
                  Players
                </button>
                <button
                  type="button"
                  className={`trade-side-dropdown-tab ${activeSearchTab === 'picks' ? 'active' : ''}`}
                  onClick={() => setActiveSearchTab('picks')}
                >
                  Draft Picks
                </button>
              </div>
            ) : null}

            {activeSearchTab === 'players' ? (
              <div className="trade-side-results-list">
                {searchQuery.trim().length < 2 ? (
                  <div className="trade-side-search-hint">
                    Type at least 2 characters to search NFL players...
                  </div>
                ) : playerSearch.loading ? (
                  Array.from({ length: 3 }).map((_, idx) => (
                    <div key={idx} className="trade-side-result-row skeleton-row">
                      <Skeleton width={28} height={28} radius={4} />
                      <div style={{ flex: 1 }}>
                        <Skeleton width={120} height={14} />
                        <Skeleton width={80} height={11} />
                      </div>
                    </div>
                  ))
                ) : playerSearch.data.length > 0 ? (
                  playerSearch.data.map((player) => {
                    const val = valueBasis === 'ktc' ? player.ktc_value : player.fc_value;
                    return (
                      <button
                        key={player.player_id}
                        type="button"
                        className="trade-side-result-row"
                        onClick={() => handleSelectPlayer(player)}
                      >
                        <div className="trade-side-result-player">
                          <PlayerAvatar
                            playerId={player.player_id}
                            name={player.name}
                            size="sm"
                          />
                          <div className="trade-side-result-copy">
                            <strong>{player.name}</strong>
                            <div className="trade-side-result-meta">
                              <span style={{ color: getPositionColor(player.position) }}>
                                {player.position}
                              </span>
                              {player.team ? (
                                <>
                                  <span>·</span>
                                  <TeamBadge team={player.team} size="xs" />
                                </>
                              ) : null}
                              {player.age != null ? (
                                <>
                                  <span>·</span>
                                  <span>{player.age} y.o.</span>
                                </>
                              ) : null}
                            </div>
                          </div>
                        </div>
                        <span className="trade-side-result-value">
                          {formatMarketValue(val ?? 0)}
                        </span>
                      </button>
                    );
                  })
                ) : (
                  <div className="trade-side-search-hint">No matching players found.</div>
                )}
              </div>
            ) : (
              <div className="trade-side-picks-panel">
                <div className="trade-side-quick-picks">
                  <span className="trade-side-picks-subtitle">Quick Add Picks:</span>
                  <div className="trade-side-quick-picks-grid">
                    {validPickYears.map((year) =>
                      [1, 2, 3, 4].map((round) => (
                        <button
                          key={`${year}-${round}`}
                          type="button"
                          className="trade-side-quick-pick-btn"
                          onClick={() => handleSelectQuickPick(year, round)}
                        >
                          <Plus size={11} /> {year} Round {round}
                        </button>
                      )),
                    )}
                  </div>
                </div>

                <div className="trade-side-custom-pick">
                  <span className="trade-side-picks-subtitle">Custom Pick with Slot:</span>
                  <div className="trade-side-custom-pick-inputs">
                    <select
                      value={customPickSeason}
                      onChange={(e) => setCustomPickSeason(e.target.value)}
                    >
                      {validPickYears.map((year) => (
                        <option key={year} value={year}>
                          {year}
                        </option>
                      ))}
                    </select>
                    <select
                      value={customPickRound}
                      onChange={(e) => setCustomPickRound(Number(e.target.value))}
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 8].map((round) => (
                        <option key={round} value={round}>
                          Round {round}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      placeholder="Slot (opt)"
                      value={customPickSlot}
                      onChange={(e) => setCustomPickSlot(e.target.value)}
                      min="1"
                      max="32"
                    />
                    <button
                      type="button"
                      className="button-primary trade-side-add-pick-btn"
                      onClick={handleAddCustomPick}
                    >
                      Add Pick
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>

      {/* Asset Cards List */}
      <div className="trade-side-asset-list">
        {assets.length === 0 ? (
          <div className="trade-side-empty-list">
            <span>No players or picks added yet</span>
            <small>Use the search bar above to add assets</small>
          </div>
        ) : (
          assets.map((asset) => (
            <div key={asset.id} className="trade-side-asset-item">
              <div className="trade-side-asset-info">
                <strong className="trade-side-asset-name">{asset.label}</strong>
                <div className="trade-side-asset-subline">
                  {asset.type === 'player' ? (
                    <>
                      <span style={{ color: getPositionColor(asset.position) }}>
                        {asset.underdogRank ?? asset.position ?? '—'}
                      </span>
                      {asset.team ? (
                        <>
                          <span>·</span>
                          <TeamBadge team={asset.team} size="xs" />
                        </>
                      ) : null}
                      {asset.age != null ? (
                        <>
                          <span>·</span>
                          <span>{asset.age} y.o.</span>
                        </>
                      ) : null}
                    </>
                  ) : (
                    <>
                      <Calendar size={11} className="trade-side-pick-icon" />
                      <span>PICK</span>
                      <span>·</span>
                      <span>{asset.meta}</span>
                    </>
                  )}
                </div>
              </div>

              <div className="trade-side-asset-end">
                <span className="trade-side-asset-value">
                  {formatMarketValue(asset.value)}
                </span>
                <button
                  type="button"
                  className="trade-side-asset-remove"
                  onClick={() => onRemoveAsset(asset.id)}
                  title={`Remove ${asset.label}`}
                  aria-label={`Remove ${asset.label}`}
                >
                  <X size={14} />
                </button>
              </div>
            </div>
          ))
        )}

        {/* Value Adjustment Card */}
        {adjustmentValue !== 0 ? (
          <div className="trade-side-adjustment-card">
            <span className="trade-side-adjustment-title">{adjustmentLabel}</span>
            <span className="trade-side-adjustment-value">
              {adjustmentValue > 0 ? `+${formatMarketValue(adjustmentValue)}` : formatMarketValue(adjustmentValue)}
            </span>
          </div>
        ) : null}
      </div>

      {/* Footer Summary */}
      <div className="trade-side-footer">
        <div className="trade-side-footer-summary">
          <span className="trade-side-piece-total">
            {assets.length} {assets.length === 1 ? 'Total Piece' : 'Total Pieces'}
          </span>
          <small className="trade-side-piece-breakdown">{pieceSummary}</small>
        </div>
        <div className="trade-side-footer-total">
          <strong className="trade-side-total-value">
            {formatMarketValue(netValue || totalValue)}
          </strong>
        </div>
      </div>
    </div>
  );
}
