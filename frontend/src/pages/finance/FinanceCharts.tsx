import { useState } from 'react';
import type {
  FinanceLeagueSeasonEntry,
} from '@/types';
import {
  buildCurrentFinanceTimeline,
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
}

function FinanceInteractiveLineChart({
  points,
  showActual,
  actualLabel,
  projectedLabel,
  anchorZero = true,
}: {
  points: FinanceLinePointData[];
  showActual: boolean;
  actualLabel: string;
  projectedLabel: string;
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
    ...(showActual ? points.map((p) => p.actual ?? 0) : []),
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

  const actualLinePoints = showActual
    ? points.map((p, i) => `${toX(i)},${toY(p.actual ?? 0)}`).join(' ')
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

        {/* Actual Line */}
        {showActual && actualLinePoints ? (
          <>
            <polyline
              fill="none"
              stroke="var(--finance-actual-color, #14b8a6)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={actualLinePoints}
            />
            {points.map((point, i) => (
              <circle
                key={`act-dot-${point.key}`}
                cx={toX(i)}
                cy={toY(point.actual ?? 0)}
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
            {showActual ? (
              <circle
                cx={hoveredX}
                cy={toY(hoveredPoint.actual ?? 0)}
                r="5.5"
                fill="var(--finance-actual-color, #14b8a6)"
                stroke="var(--color-surface, #0f172a)"
                strokeWidth="2"
                pointerEvents="none"
              />
            ) : null}
          </>
        ) : null}

        {/* Hover Tooltip */}
        {hoveredIndex !== null && hoveredPoint && hoveredX !== null ? (() => {
          const tooltipWidth = 148;
          const tooltipHeight = showActual ? 54 : 38;
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
              <text
                x={10}
                y={28}
                fill="var(--finance-projected-color, #a855f7)"
                fontSize="11px"
                fontWeight="500"
                fontFamily="inherit"
              >
                {projectedLabel}: {formatCurrency(hoveredPoint.projected)}
              </text>
              {showActual ? (
                <text
                  x={10}
                  y={44}
                  fill="var(--finance-actual-color, #14b8a6)"
                  fontSize="11px"
                  fontWeight="500"
                  fontFamily="inherit"
                >
                  {actualLabel}: {formatCurrency(hoveredPoint.actual ?? 0)}
                </text>
              ) : null}
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
}: {
  entries: FinanceChartEntry[];
}) {
  const points = entries.map((entry) => ({
    key: entry.key,
    label: entry.label,
    actual: entry.winningsAmount,
    projected: entry.projectedWinningsAmount,
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
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-actual" />
          Finish payout
        </span>
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-projected" />
          Projected payout
        </span>
      </div>

      <FinanceInteractiveLineChart
        points={points}
        showActual={true}
        actualLabel="Finish"
        projectedLabel="Projected"
        anchorZero={true}
      />
    </article>
  );
}

export function FinanceProjectionTimeline({
  entries,
  season,
  timeline,
}: {
  entries: FinanceLeagueSeasonEntry[];
  season: string;
  timeline?: FinanceTimelinePoint[];
}) {
  const timelinePoints = timeline && timeline.length ? timeline : buildCurrentFinanceTimeline(entries);
  const isComplete = entries.length > 0 && entries.every(isFinanceSeasonComplete);
  const showActualPayout = isComplete && timelinePoints.some((point) => (point.actualAmount ?? 0) > 0);

  const points = timelinePoints.map((point) => ({
    key: point.week,
    label: point.label,
    actual: point.actualAmount,
    projected: point.projectedAmount,
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
      </div>

      <FinanceInteractiveLineChart
        points={points}
        showActual={showActualPayout}
        actualLabel="Actual"
        projectedLabel="Expected"
        anchorZero={showActualPayout}
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
