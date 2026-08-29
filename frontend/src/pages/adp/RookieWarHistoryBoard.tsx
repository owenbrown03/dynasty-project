import React, {
  useMemo,
  useState,
} from 'react';
import { Loader2 } from 'lucide-react';

import { Skeleton } from '@/components/feedback/Skeleton';
import { useRookieWarHistory } from '@/hooks/useRookieWarHistory';
import { useLeagueOverview } from '@/hooks/sleeper/useLeagues';
import type { RookieWarHistoryRow } from '@/types';
import { formatNumber } from '@/utils/format';

import './RookieWarHistoryBoard.css';

interface PickSlotSummary {
  round: number;
  slot: number;
  pickLabel: string;
  avgWar: number | null;
  smoothWar: number | null;
  medWar: number | null;
  hitRate: number | null;
  bustRate: number | null;
  byYear: Record<number, RookieWarHistoryRow>;
}

function smoothRookieWarCurve(
  values: number[],
  sigma = 2.0,
  minDecaySlope = 0.01,
): number[] {
  const n = values.length;
  if (n === 0) return [];

  // 1. Gaussian kernel smoothing
  const kernelSmoothed: number[] = [];
  for (let i = 0; i < n; i += 1) {
    let totalWeight = 0;
    let weightedSum = 0;
    for (let j = 0; j < n; j += 1) {
      const w = Math.exp(-((i - j) ** 2) / (2 * (sigma ** 2)));
      totalWeight += w;
      weightedSum += w * values[j];
    }
    kernelSmoothed.push(weightedSum / totalWeight);
  }

  // 2. PAVA with minDecaySlope constraint: y[i] >= y[i+1] + minDecaySlope
  const transformed = kernelSmoothed.map((v, i) => v + i * minDecaySlope);
  const blocks: { weight: number; count: number; indices: number[] }[] = transformed.map(
    (v, i) => ({ weight: -v, count: 1, indices: [i] }),
  );

  let i = 0;
  while (i < blocks.length - 1) {
    if (blocks[i].weight > blocks[i + 1].weight) {
      const b1 = blocks[i];
      const b2 = blocks[i + 1];
      const newWeight = (b1.weight * b1.count + b2.weight * b2.count) / (b1.count + b2.count);
      blocks[i] = {
        weight: newWeight,
        count: b1.count + b2.count,
        indices: [...b1.indices, ...b2.indices],
      };
      blocks.splice(i + 1, 1);
      if (i > 0) {
        i -= 1;
      }
    } else {
      i += 1;
    }
  }

  const result: number[] = new Array(n).fill(0);
  for (const block of blocks) {
    for (const idx of block.indices) {
      result[idx] = Number((-block.weight - idx * minDecaySlope).toFixed(2));
    }
  }
  return result;
}

function HistoryTableSkeleton({
  withWar,
}: {
  withWar: boolean;
}) {
  const columns = withWar ? 9 : 6;
  return (
    <div className="rkwh-table-card" role="status" aria-live="polite">
      <div className="rkwh-table-header">
        <Skeleton width={160} variant="title" />
        <Skeleton width={120} variant="text" />
      </div>
      <div className="rkwh-table-scroll">
        <table className="rkwh-table">
          <thead>
            <tr>
              {
                Array.from({ length: columns }).map((_, index) => (
                  <th key={index}><Skeleton width={64} variant="text" /></th>
                ))
              }
            </tr>
          </thead>
          <tbody>
            {
              Array.from({ length: 8 }).map((__, rowIndex) => (
                <tr key={rowIndex}>
                  {
                    Array.from({ length: columns }).map((_, colIndex) => (
                      <td key={colIndex}><Skeleton width={52} variant="text" /></td>
                    ))
                  }
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function RookieWarHistoryBoard() {
  const leagueOverview = useLeagueOverview();
  const [leagueId, setLeagueId] = useState('');
  const [selectedRound, setSelectedRound] = useState<number | 'all'>('all');
  const [metric, setMetric] = useState<'starter_war' | 'roster_war'>('roster_war');
  const [scope, setScope] = useState<'career' | 'per_year'>('career');

  const history = useRookieWarHistory(
    leagueId || undefined,
    true,
  );

  const selectedLeagueName = useMemo(
    () => leagueOverview.data.find(
      (league) => league.league_id === leagueId,
    )?.league_name ?? null,
    [leagueId, leagueOverview.data],
  );

  const rows = useMemo(
    () => history.data?.rows ?? [],
    [history.data],
  );
  const hasWar = Boolean(history.data?.has_war);

  // Extract unique sorted years
  const years = useMemo(() => {
    const set = new Set<number>();
    for (const r of rows) {
      if (r.draft_year) {
        set.add(r.draft_year);
      }
    }
    return Array.from(set).sort((a, b) => a - b);
  }, [rows]);

  // Current NFL season reference for seasons played
  const currentSeason = 2025;

  // Build 48 pick slots (Rounds 1-4, Slots 1-12) with smoothing and round filter
  const pickSlotSummaries = useMemo<PickSlotSummary[]>(() => {
    const map = new Map<string, RookieWarHistoryRow>();
    for (const r of rows) {
      map.set(`${r.draft_year}-${r.round}-${r.round_slot}`, r);
    }

    // Step 1: Precompute raw slot averages across all 48 slots for smoothing
    const all48Averages: number[] = [];
    const all48Data: {
      round: number;
      slot: number;
      pickLabel: string;
      avgWar: number | null;
      medWar: number | null;
      hitRate: number | null;
      bustRate: number | null;
      byYear: Record<number, RookieWarHistoryRow>;
    }[] = [];

    for (let rnd = 1; rnd <= 4; rnd += 1) {
      for (let sl = 1; sl <= 12; sl += 1) {
        const pickLabel = `${rnd}.${sl.toString().padStart(2, '0')}`;
        const byYear: Record<number, RookieWarHistoryRow> = {};
        const wars: number[] = [];
        const evaluatedWars: { value: number; yearsInLeague: number }[] = [];

        for (const yr of years) {
          const row = map.get(`${yr}-${rnd}-${sl}`);
          if (row) {
            byYear[yr] = row;
            const rawWar = metric === 'starter_war' ? row.starter_war : row.roster_war;
            if (rawWar != null) {
              const yearsInLeague = Math.max(0, currentSeason - yr + 1);
              const displayVal = scope === 'per_year' && yearsInLeague > 0
                ? rawWar / yearsInLeague
                : rawWar;
              wars.push(displayVal);

              if (yearsInLeague > 0) {
                evaluatedWars.push({
                  value: displayVal,
                  yearsInLeague,
                });
              }
            }
          }
        }

        let avgWar: number | null = null;
        let medWar: number | null = null;
        let hitRate: number | null = null;
        let bustRate: number | null = null;

        if (wars.length > 0) {
          const sum = wars.reduce((acc, v) => acc + v, 0);
          avgWar = sum / wars.length;
          const sortedWars = [...wars].sort((a, b) => a - b);
          const mid = Math.floor(sortedWars.length / 2);
          medWar = sortedWars.length % 2 !== 0
            ? sortedWars[mid]
            : (sortedWars[mid - 1] + sortedWars[mid]) / 2;
        }

        if (evaluatedWars.length > 0) {
          const hitThreshold = scope === 'per_year' ? 0.9 : 2.5;
          const bustThreshold = scope === 'per_year' ? 0.3 : 0.8;
          const hits = evaluatedWars.filter((e) => e.value >= hitThreshold).length;
          const busts = evaluatedWars.filter((e) => e.value <= bustThreshold).length;
          hitRate = (hits / evaluatedWars.length) * 100;
          bustRate = (busts / evaluatedWars.length) * 100;
        }

        all48Averages.push(avgWar ?? 0);
        all48Data.push({
          round: rnd,
          slot: sl,
          pickLabel,
          avgWar,
          medWar,
          hitRate,
          bustRate,
          byYear,
        });
      }
    }

    // Step 2: Smooth all 48 slots monotonically
    const smoothedValues = smoothRookieWarCurve(all48Averages);

    // Step 3: Filter to selected round(s)
    const targetRounds = selectedRound === 'all' ? [1, 2, 3, 4] : [selectedRound];
    const summaries: PickSlotSummary[] = [];

    for (let idx = 0; idx < all48Data.length; idx += 1) {
      const item = all48Data[idx];
      if (targetRounds.includes(item.round)) {
        summaries.push({
          ...item,
          smoothWar: item.avgWar != null ? smoothedValues[idx] : null,
        });
      }
    }

    return summaries;
  }, [rows, years, selectedRound, metric, scope]);

  const isLoading = history.isLoading;
  const isFetching = history.isFetching;

  return (
    <div className="rkwh-page">
      <section className="rkwh-toolbar">
        <label className="rkwh-selector">
          <span>League (WAR context)</span>
          <select
            value={leagueId}
            onChange={(event) => setLeagueId(event.target.value)}
          >
            <option value="">
              Consensus Superflex PPR (Default)
            </option>
            {
              leagueOverview.data.map((league) => (
                <option key={league.league_id} value={league.league_id}>
                  {league.league_name} (Custom Scoring)
                </option>
              ))
            }
          </select>
        </label>

        {hasWar ? (
          <>
            <div className="rkwh-toolbar-meta">
              <span className="rkwh-meta-label">Metric</span>
              <div className="rkwh-pill-group">
                <button
                  type="button"
                  className={`rkwh-filter-pill ${metric === 'roster_war' ? 'rkwh-filter-pill--active' : ''}`}
                  onClick={() => setMetric('roster_war')}
                >
                  Roster WAR
                </button>
                <button
                  type="button"
                  className={`rkwh-filter-pill ${metric === 'starter_war' ? 'rkwh-filter-pill--active' : ''}`}
                  onClick={() => setMetric('starter_war')}
                >
                  Starter WAR
                </button>
              </div>
            </div>

            <div className="rkwh-toolbar-meta">
              <span className="rkwh-meta-label">Basis</span>
              <div className="rkwh-pill-group">
                <button
                  type="button"
                  className={`rkwh-filter-pill ${scope === 'career' ? 'rkwh-filter-pill--active' : ''}`}
                  onClick={() => setScope('career')}
                >
                  Career Total
                </button>
                <button
                  type="button"
                  className={`rkwh-filter-pill ${scope === 'per_year' ? 'rkwh-filter-pill--active' : ''}`}
                  onClick={() => setScope('per_year')}
                  title="Annualized WAR per active NFL season"
                >
                  WAR / Year
                </button>
              </div>
            </div>
          </>
        ) : null}

        <div className="rkwh-toolbar-meta">
          <span className="rkwh-meta-label">Rounds</span>
          <div className="rkwh-pill-group">
            <button
              type="button"
              className={`rkwh-filter-pill ${selectedRound === 'all' ? 'rkwh-filter-pill--active' : ''}`}
              onClick={() => setSelectedRound('all')}
            >
              All (48)
            </button>
            {[1, 2, 3, 4].map((rnd) => (
              <button
                key={rnd}
                type="button"
                className={`rkwh-filter-pill ${selectedRound === rnd ? 'rkwh-filter-pill--active' : ''}`}
                onClick={() => setSelectedRound(rnd)}
              >
                Rd {rnd}
              </button>
            ))}
          </div>
        </div>
      </section>

      {
        !hasWar && !isLoading ? (
          <div className="rkwh-hint">
            This board shows historical consensus rookie draft selections.
            Select a league above to compute each player's career <strong>roster</strong> and <strong>starter</strong>{' '}
            WAR under that league's custom scoring settings.
          </div>
        ) : null
      }

      {
        isFetching && !isLoading ? (
          <div className="rkwh-refreshing">
            <Loader2 size={14} className="rkwh-spin" />
            Updating WAR...
          </div>
        ) : null
      }

      {
        isLoading && !history.data
          ? <HistoryTableSkeleton withWar={hasWar} />
          : (
            <div className="rkwh-table-card">
              <div className="rkwh-table-header">
                <div className="rkwh-table-header-title">
                  <strong>Rookie Pick WAR History Board</strong>
                  <small>
                    {hasWar
                      ? `${scope === 'per_year' ? 'Annualized WAR / Year' : 'Career Total WAR'} (${metric === 'roster_war' ? 'Roster' : 'Starter'}) under ${selectedLeagueName ?? 'Consensus Superflex PPR'}`
                      : 'Consensus draft selections across historical rookie classes'}
                  </small>
                </div>
              </div>

              <div className="rkwh-table-scroll">
                <table className="rkwh-table rkwh-board-matrix">
                  <thead>
                    <tr className="rkwh-head-row">
                      <th className="rkwh-freeze-col rkwh-col-pick">Pick</th>
                      {hasWar ? (
                        <>
                          <th className="rkwh-freeze-col rkwh-col-avg" title="Raw historical arithmetic mean">Avg</th>
                          <th className="rkwh-freeze-col rkwh-col-smooth" title="Smoothed monotonic expected WAR accounting for sample size & slot hierarchy">Smooth</th>
                          <th className="rkwh-freeze-col rkwh-col-med" title="Historical median WAR">Med</th>
                          <th className="rkwh-freeze-col rkwh-col-hit" title="Hit percentage (% with >= 2.5 career WAR or 0.9 WAR/yr)">Hit</th>
                          <th className="rkwh-freeze-col rkwh-col-bust" title="Bust percentage (% with <= 0.8 career WAR or 0.3 WAR/yr)">Bust</th>
                        </>
                      ) : null}
                      {years.map((year) => (
                        <React.Fragment key={year}>
                          <th className="rkwh-th-year-player">{year}</th>
                          {hasWar ? <th className="rkwh-th-year-war">{scope === 'per_year' ? 'WAR/yr' : 'WAR'}</th> : null}
                        </React.Fragment>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {pickSlotSummaries.map((summary) => (
                      <tr key={summary.pickLabel} className="rkwh-matrix-row">
                        <td className="rkwh-freeze-col rkwh-col-pick rkwh-pick-label">
                          {summary.pickLabel}
                        </td>
                        {hasWar ? (
                          <>
                            <td className="rkwh-freeze-col rkwh-col-avg rkwh-stat-num">
                              {summary.avgWar != null ? formatNumber(summary.avgWar) : '—'}
                            </td>
                            <td className="rkwh-freeze-col rkwh-col-smooth rkwh-stat-num rkwh-stat-smooth">
                              {summary.smoothWar != null ? (
                                <strong className="rkwh-smooth-val">
                                  {formatNumber(summary.smoothWar)}
                                </strong>
                              ) : '—'}
                            </td>
                            <td className="rkwh-freeze-col rkwh-col-med rkwh-stat-num">
                              {summary.medWar != null ? formatNumber(summary.medWar) : '—'}
                            </td>
                            <td className="rkwh-freeze-col rkwh-col-hit rkwh-stat-num">
                              {summary.hitRate != null ? (
                                <span className={`rkwh-rate-tag ${summary.hitRate >= 50 ? 'rkwh-rate-tag--high' : ''}`}>
                                  {Math.round(summary.hitRate)}%
                                </span>
                              ) : '—'}
                            </td>
                            <td className="rkwh-freeze-col rkwh-col-bust rkwh-stat-num">
                              {summary.bustRate != null ? (
                                <span className={`rkwh-rate-tag ${summary.bustRate >= 50 ? 'rkwh-rate-tag--bust' : ''}`}>
                                  {Math.round(summary.bustRate)}%
                                </span>
                              ) : '—'}
                            </td>
                          </>
                        ) : null}

                        {years.map((year) => {
                          const p = summary.byYear[year];
                          if (!p) {
                            return (
                              <React.Fragment key={year}>
                                <td className="rkwh-matrix-cell rkwh-player-box-cell">—</td>
                                {hasWar ? <td className="rkwh-matrix-cell rkwh-war-val-cell">—</td> : null}
                              </React.Fragment>
                            );
                          }
                          const pos = p.position ?? '??';
                          const rawWar = metric === 'starter_war' ? p.starter_war : p.roster_war;
                          const yearsInLeague = Math.max(0, currentSeason - year + 1);
                          const warVal = rawWar != null && scope === 'per_year' && yearsInLeague > 0
                            ? rawWar / yearsInLeague
                            : rawWar;
                          const hitThresh = scope === 'per_year' ? 0.9 : 2.5;
                          const bustThresh = scope === 'per_year' ? 0.3 : 0.8;

                          return (
                            <React.Fragment key={year}>
                              <td className="rkwh-matrix-cell rkwh-player-box-cell">
                                <div className="rkwh-player-box">
                                  <span className={`rkwh-pos-tag rkwh-pos-tag--${pos.toLowerCase()}`}>
                                    {pos}
                                  </span>
                                  <span className="rkwh-player-name-text" title={p.name}>
                                    {p.name}
                                  </span>
                                </div>
                              </td>
                              {hasWar ? (
                                <td className="rkwh-matrix-cell rkwh-war-val-cell">
                                  {warVal != null ? (
                                    <span className={`rkwh-war-score ${warVal >= hitThresh ? 'rkwh-war-score--hit' : (warVal <= bustThresh ? 'rkwh-war-score--bust' : '')}`}>
                                      {formatNumber(warVal)}
                                    </span>
                                  ) : '—'}
                                </td>
                              ) : null}
                            </React.Fragment>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )
      }
    </div>
  );
}
