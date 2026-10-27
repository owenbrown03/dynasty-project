import { useState } from 'react';
import { Skeleton } from '@/components/feedback/Skeleton';
import type {
  FinanceLeagueSeasonEntry,
} from '@/types';
import {
  effectiveFinanceNet,
  effectiveFinanceWinnings,
  financeResultLabel,
  formatCurrency,
  getDraftKey,
  isFinanceSeasonComplete,
  type FinanceChartEntry,
  type FinanceTimelinePoint,
} from './finance.utils';

function formatCompactCurrency(val: number): string {
  if (Math.abs(val) >= 1000) {
    const k = val / 1000;
    return `$${k % 1 === 0 ? k.toFixed(0) : k.toFixed(1)}k`;
  }
  return `$${Math.round(val)}`;
}

interface FinanceLinePointData {
  key: string | number;
  label: string;
  actual?: number | null;
  projected: number;
  buyIn?: number | null;
}

function FinanceInteractiveLineChart({
  points,
  showActual,
  actualLabel,
  projectedLabel,
  showBuyIn = false,
  buyInLabel = 'Buy-in',
  anchorZero = true,
}: {
  points: FinanceLinePointData[];
  showActual: boolean;
  actualLabel: string;
  projectedLabel: string;
  showBuyIn?: boolean;
  buyInLabel?: string;
  anchorZero?: boolean;
}) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (!points.length) {
    return null;
  }

  const CHART_WIDTH = 380;
  const CHART_HEIGHT = 160;
  const PADDING_LEFT = 52;
  const PADDING_RIGHT = 18;
  const PADDING_TOP = 16;
  const PADDING_BOTTOM = 26;

  const plotWidth = CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT;
  const plotHeight = CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM;

  const allValues = [
    ...points.map((p) => p.projected),
    ...(showActual
      ? points
          .filter((p) => p.actual !== null && p.actual !== undefined)
          .map((p) => p.actual as number)
      : []),
    ...(showBuyIn ? points.map((p) => p.buyIn ?? 0) : []),
  ];

  let minValue = anchorZero ? Math.min(...allValues, 0) : Math.min(...allValues);
  let maxValue = Math.max(...allValues, 1);

  if (!anchorZero && maxValue > minValue) {
    const pad = (maxValue - minValue) * 0.15;
    minValue = Math.max(0, minValue - pad);
    maxValue = maxValue + pad;
  }

  const range = maxValue - minValue || 1;

  const toX = (index: number) => {
    if (points.length <= 1) {
      return PADDING_LEFT + plotWidth / 2;
    }
    return PADDING_LEFT + (index / (points.length - 1)) * plotWidth;
  };

  const toY = (val: number) => {
    return PADDING_TOP + plotHeight - ((val - minValue) / range) * plotHeight;
  };

  const yTicks = [
    minValue,
    minValue + range / 3,
    minValue + (2 * range) / 3,
    maxValue,
  ];

  const projectedLinePoints = points
    .map((p, i) => `${toX(i)},${toY(p.projected)}`)
    .join(' ');

  const pointsWithActual = points
    .map((p, i) => ({
      ...p,
      x: toX(i),
      y: p.actual !== null && p.actual !== undefined ? toY(p.actual) : 0,
    }))
    .filter((p) => p.actual !== null && p.actual !== undefined);

  const actualLinePoints = showActual && pointsWithActual.length > 0
    ? pointsWithActual.map((p) => `${p.x},${p.y}`).join(' ')
    : '';

  const buyInLinePoints = showBuyIn
    ? points.map((p, i) => `${toX(i)},${toY(p.buyIn ?? 0)}`).join(' ')
    : '';

  const hoveredPoint = hoveredIndex !== null ? points[hoveredIndex] : null;
  const hoveredX = hoveredIndex !== null ? toX(hoveredIndex) : null;

  return (
    <div className="finance-line-chart">
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        aria-hidden="true"
        onMouseLeave={() => setHoveredIndex(null)}
      >
        {/* Horizontal grid lines & Y-axis scale */}
        {yTicks.map((tick, i) => {
          const y = toY(tick);
          return (
            <g key={i}>
              <line
                x1={PADDING_LEFT}
                y1={y}
                x2={CHART_WIDTH - PADDING_RIGHT}
                y2={y}
                stroke="var(--color-border-subtle, rgba(255,255,255,0.08))"
                strokeDasharray="3 3"
              />
              <text
                x={PADDING_LEFT - 8}
                y={y + 3.5}
                textAnchor="end"
                fill="var(--color-text-muted, #94a3b8)"
                fontSize="10px"
                fontFamily="inherit"
              >
                {formatCompactCurrency(tick)}
              </text>
            </g>
          );
        })}

        {/* X-axis labels */}
        {points.map((point, i) => (
          <text
            key={point.key}
            x={toX(i)}
            y={CHART_HEIGHT - 8}
            textAnchor="middle"
            fill={
              hoveredIndex === i
                ? 'var(--color-text-primary, #ffffff)'
                : 'var(--color-text-muted, #94a3b8)'
            }
            fontSize="11px"
            fontWeight={hoveredIndex === i ? '600' : '400'}
            fontFamily="inherit"
          >
            {point.label}
          </text>
        ))}

        {/* Buy-in Line */}
        {showBuyIn && buyInLinePoints ? (
          <>
            <polyline
              fill="none"
              stroke="var(--finance-buy-in-color, #60a5fa)"
              strokeWidth="2"
              strokeDasharray="2 4"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={buyInLinePoints}
            />
            {points.map((point, i) => (
              <circle
                key={`buyin-dot-${point.key}`}
                cx={toX(i)}
                cy={toY(point.buyIn ?? 0)}
                r="3"
                fill="var(--finance-buy-in-color, #60a5fa)"
              />
            ))}
          </>
        ) : null}

        {/* Actual Line */}
        {showActual && actualLinePoints ? (
          <>
            {pointsWithActual.length > 1 ? (
              <polyline
                fill="none"
                stroke="var(--finance-actual-color, #14b8a6)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={actualLinePoints}
              />
            ) : null}
            {pointsWithActual.map((point) => (
              <circle
                key={`act-dot-${point.key}`}
                cx={point.x}
                cy={point.y}
                r="3"
                fill="var(--finance-actual-color, #14b8a6)"
              />
            ))}
          </>
        ) : null}

        {/* Projected Line */}
        <polyline
          fill="none"
          stroke="var(--finance-projected-color, #a855f7)"
          strokeWidth="2.5"
          strokeDasharray="5 5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={projectedLinePoints}
        />
        {points.map((point, i) => (
          <circle
            key={`proj-dot-${point.key}`}
            cx={toX(i)}
            cy={toY(point.projected)}
            r="3"
            fill="var(--finance-projected-color, #a855f7)"
          />
        ))}

        {/* Hover vertical guide line */}
        {hoveredX !== null ? (
          <line
            x1={hoveredX}
            y1={PADDING_TOP}
            x2={hoveredX}
            y2={PADDING_TOP + plotHeight}
            stroke="var(--color-border-strong, rgba(255,255,255,0.25))"
            strokeDasharray="2 2"
            strokeWidth="1.5"
            pointerEvents="none"
          />
        ) : null}

        {/* Hovered point circles */}
        {hoveredIndex !== null && hoveredPoint && hoveredX !== null ? (
          <>
            <circle
              cx={hoveredX}
              cy={toY(hoveredPoint.projected)}
              r="5.5"
              fill="var(--finance-projected-color, #a855f7)"
              stroke="var(--color-surface, #0f172a)"
              strokeWidth="2"
              pointerEvents="none"
            />
            {showActual && hoveredPoint.actual !== null && hoveredPoint.actual !== undefined ? (
              <circle
                cx={hoveredX}
                cy={toY(hoveredPoint.actual)}
                r="5.5"
                fill="var(--finance-actual-color, #14b8a6)"
                stroke="var(--color-surface, #0f172a)"
                strokeWidth="2"
                pointerEvents="none"
              />
            ) : null}
            {showBuyIn && hoveredPoint.buyIn !== undefined && hoveredPoint.buyIn !== null ? (
              <circle
                cx={hoveredX}
                cy={toY(hoveredPoint.buyIn)}
                r="5.5"
                fill="var(--finance-buy-in-color, #60a5fa)"
                stroke="var(--color-surface, #0f172a)"
                strokeWidth="2"
                pointerEvents="none"
              />
            ) : null}
          </>
        ) : null}

        {/* Hover Tooltip */}
        {hoveredIndex !== null && hoveredPoint && hoveredX !== null ? (() => {
          const lines: { label: string; value: number; color: string }[] = [];
          lines.push({
            label: projectedLabel,
            value: hoveredPoint.projected,
            color: 'var(--finance-projected-color, #a855f7)',
          });
          if (showActual && hoveredPoint.actual !== null && hoveredPoint.actual !== undefined) {
            lines.push({
              label: actualLabel,
              value: hoveredPoint.actual,
              color: 'var(--finance-actual-color, #14b8a6)',
            });
          }
          if (showBuyIn && hoveredPoint.buyIn !== undefined && hoveredPoint.buyIn !== null) {
            lines.push({
              label: buyInLabel,
              value: hoveredPoint.buyIn,
              color: 'var(--finance-buy-in-color, #60a5fa)',
            });
          }

          const tooltipWidth = 152;
          const tooltipHeight = 20 + lines.length * 16;
          const tooltipX =
            hoveredX > CHART_WIDTH / 2
              ? hoveredX - tooltipWidth - 10
              : hoveredX + 10;
          const tooltipY = Math.min(
            Math.max(toY(hoveredPoint.projected) - tooltipHeight / 2, PADDING_TOP),
            CHART_HEIGHT - PADDING_BOTTOM - tooltipHeight
          );

          return (
            <g
              transform={`translate(${tooltipX}, ${tooltipY})`}
              pointerEvents="none"
            >
              <rect
                width={tooltipWidth}
                height={tooltipHeight}
                rx={6}
                fill="var(--color-surface-raised, #1e293b)"
                stroke="var(--color-border-subtle, rgba(255,255,255,0.15))"
                strokeWidth="1"
              />
              <text
                x={10}
                y={14}
                fill="var(--color-text-muted, #94a3b8)"
                fontSize="11px"
                fontWeight="600"
                fontFamily="inherit"
              >
                {hoveredPoint.label}
              </text>
              {lines.map((line, idx) => (
                <text
                  key={line.label}
                  x={10}
                  y={28 + idx * 15}
                  fill={line.color}
                  fontSize="11px"
                  fontWeight="500"
                  fontFamily="inherit"
                >
                  {line.label}: {formatCurrency(line.value)}
                </text>
              ))}
            </g>
          );
        })() : null}

        {/* Interactive hover column slices */}
        {points.map((point, i) => {
          const sliceWidth =
            points.length <= 1 ? plotWidth : plotWidth / (points.length - 1);
          const sliceX =
            points.length <= 1
              ? PADDING_LEFT
              : toX(i) - sliceWidth / 2;

          return (
            <rect
              key={`slice-${point.key}`}
              x={sliceX}
              y={PADDING_TOP}
              width={sliceWidth}
              height={plotHeight}
              fill="transparent"
              style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHoveredIndex(i)}
            />
          );
        })}
      </svg>
    </div>
  );
}

export function FinanceTrendChart({
  entries,
  isLoading = false,
}: {
  entries: FinanceChartEntry[];
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <article className="finance-chart-card" aria-busy="true">
        <div className="finance-chart-header">
          <div>
            <p className="finance-chart-kicker">Trend</p>
            <h2>Results vs projected winnings</h2>
          </div>
        </div>
        <div className="finance-skeleton-chart">
          <Skeleton width="100%" height={160} />
        </div>
      </article>
    );
  }

  const showBuyIn = entries.some((entry) => (entry.buyInAmount ?? 0) > 0);
  const showActual = entries.some(
    (entry) => entry.actualWinningsAmount !== null && entry.actualWinningsAmount !== undefined,
  );
  const points = entries.map((entry) => ({
    key: entry.key,
    label: entry.label,
    actual: entry.actualWinningsAmount ?? null,
    projected: entry.projectedWinningsAmount,
    buyIn: entry.buyInAmount,
  }));

  return (
    <article className="finance-chart-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">Trend</p>
          <h2>Results vs projected winnings</h2>
        </div>
      </div>

      <div className="finance-chart-legend">
        {showActual ? (
          <span className="finance-legend-item">
            <i className="finance-legend-line finance-legend-line-actual" />
            Finish payout
          </span>
        ) : null}
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-projected" />
          Projected payout
        </span>
        {showBuyIn ? (
          <span className="finance-legend-item">
            <i className="finance-legend-line finance-legend-line-buyin" />
            Buy-in
          </span>
        ) : null}
      </div>

      <FinanceInteractiveLineChart
        points={points}
        showActual={showActual}
        actualLabel="Finish"
        projectedLabel="Projected"
        showBuyIn={showBuyIn}
        buyInLabel="Buy-in"
        anchorZero={true}
      />
    </article>
  );
}

export function FinanceProjectionTimeline({
  entries,
  season,
  timeline,
  isLoading = false,
}: {
  entries: FinanceLeagueSeasonEntry[];
  season: string;
  timeline?: FinanceTimelinePoint[];
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <article className="finance-chart-card" aria-busy="true">
        <div className="finance-chart-header">
          <div>
            <p className="finance-chart-kicker">Weekly projection</p>
            <h2>{season} payout trajectory</h2>
          </div>
        </div>
        <div className="finance-skeleton-chart">
          <Skeleton width="100%" height={160} />
        </div>
        <div className="finance-timeline-note">
          <Skeleton width={120} height={24} />
          <Skeleton width="80%" height={14} />
        </div>
      </article>
    );
  }

  const timelinePoints = timeline && timeline.length ? timeline : [];
  if (!timelinePoints.length) {
    return (
      <article className="finance-chart-card">
        <div className="finance-chart-header">
          <div>
            <p className="finance-chart-kicker">Weekly projection</p>
            <h2>{season} payout trajectory</h2>
          </div>
        </div>
        <div
          style={{
            padding: '48px 16px',
            textAlign: 'center',
            color: 'var(--color-text-muted)',
            fontSize: '13px',
          }}
        >
          No weekly trajectory data available for {season}.
        </div>
      </article>
    );
  }

  const isComplete = entries.length > 0 && entries.every(isFinanceSeasonComplete);
  const showActualPayout = isComplete && timelinePoints.some((point) => (point.actualAmount ?? 0) > 0);
  const totalBuyIn = entries.reduce((sum, e) => sum + (e.buy_in_amount || 0), 0);
  const showBuyIn = totalBuyIn > 0;

  const points = timelinePoints.map((point) => ({
    key: point.week,
    label: point.label,
    actual: point.actualAmount,
    projected: point.projectedAmount,
    buyIn: showBuyIn ? totalBuyIn : undefined,
  }));

  const latest = points[points.length - 1];

  return (
    <article className="finance-chart-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">Weekly projection</p>
          <h2>{season} payout trajectory</h2>
        </div>
      </div>

      <div className="finance-chart-legend">
        {showActualPayout ? (
          <span className="finance-legend-item">
            <i className="finance-legend-line finance-legend-line-actual" />
            Actual payout
          </span>
        ) : null}
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-projected" />
          Expected payout
        </span>
        {showBuyIn ? (
          <span className="finance-legend-item">
            <i className="finance-legend-line finance-legend-line-buyin" />
            Buy-in
          </span>
        ) : null}
      </div>

      <FinanceInteractiveLineChart
        points={points}
        showActual={showActualPayout}
        actualLabel="Actual"
        projectedLabel="Expected"
        showBuyIn={showBuyIn}
        buyInLabel="Buy-in"
        anchorZero={showActualPayout || showBuyIn}
      />

      <div className="finance-timeline-note">
        <strong>
          {
            latest
              ? formatCurrency(latest.projected)
              : formatCurrency(0)
          }
        </strong>
        <span>
          Weekly payout trajectory computed from current standings and
          projected finish probabilities.
        </span>
      </div>
    </article>
  );
}

export function FinanceNetChart({
  entries,
}: {
  entries: FinanceChartEntry[];
}) {
  const sortedEntries = [...entries].sort((left, right) => (
    Number(right.label) - Number(left.label)
  ));
  const maxMagnitude = Math.max(
    ...sortedEntries.map((entry) => Math.abs(entry.netAmount)),
    1,
  );

  return (
    <article className="finance-chart-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">Net</p>
          <h2>Season net results</h2>
        </div>
      </div>

      <div className="finance-bar-chart">
        {
          sortedEntries.map((entry) => (
            <div
              key={entry.key}
              className="finance-bar-row"
            >
              <div className="finance-bar-copy">
                <strong>{entry.label}</strong>
                <span>{entry.subLabel}</span>
              </div>

              <div className="finance-bar-track">
                <div
                  className={
                    entry.netAmount >= 0
                      ? 'finance-bar finance-bar-positive'
                      : 'finance-bar finance-bar-negative'
                  }
                  style={{
                    width: `${(Math.abs(entry.netAmount) / maxMagnitude) * 100}%`,
                  }}
                />
              </div>

              <strong className="finance-bar-value">
                {formatCurrency(entry.netAmount)}
              </strong>
            </div>
          ))
        }
      </div>
    </article>
  );
}

export function FinanceLeagueBreakdown({
  entries,
}: {
  entries: FinanceLeagueSeasonEntry[];
}) {
  const sortedEntries = [...entries].sort((left, right) => (
    effectiveFinanceNet(right) - effectiveFinanceNet(left)
  ));
  const hasProjectedEntries = entries.some((entry) => (
    !isFinanceSeasonComplete(entry)
  ));

  return (
    <article className="finance-chart-card finance-league-breakdown-card">
      <div className="finance-chart-header">
        <div>
          <p className="finance-chart-kicker">League results</p>
          <h2>League net breakdown</h2>
          {
            hasProjectedEntries
              ? (
                <p className="finance-chart-note">
                  Active seasons use projected/expected payouts until final results are complete.
                </p>
              )
              : null
          }
        </div>
      </div>

      <div className="finance-league-breakdown">
        {
          sortedEntries.map((entry) => (
            <div
              key={getDraftKey(entry)}
              className="finance-league-breakdown-row"
            >
              <div>
                <strong>{entry.league_name}</strong>
                <span>{financeResultLabel(entry)}</span>
              </div>
              <div>
                <span>
                  {
                    isFinanceSeasonComplete(entry)
                      ? 'Net'
                      : 'Projected net'
                  }
                </span>
                <strong>{formatCurrency(effectiveFinanceNet(entry))}</strong>
              </div>
              <div>
                <span>
                  {
                    isFinanceSeasonComplete(entry)
                      ? 'Finish payout'
                      : 'Expected payout'
                  }
                </span>
                <strong>{formatCurrency(effectiveFinanceWinnings(entry))}</strong>
              </div>
              <div>
                <span>Buy-in</span>
                <strong>{formatCurrency(entry.buy_in_amount)}</strong>
              </div>
            </div>
          ))
        }
      </div>
    </article>
  );
}
