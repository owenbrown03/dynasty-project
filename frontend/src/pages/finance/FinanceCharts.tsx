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
} from './finance.utils';

function buildLinePoints(
  values: number[],
  width: number,
  height: number,
) {
  if (!values.length) {
    return '';
  }

  const minValue = Math.min(...values, 0);
  const maxValue = Math.max(...values, 1);
  const range = maxValue - minValue || 1;

  return values.map((value, index) => {
    const x = values.length === 1
      ? width / 2
      : (index / (values.length - 1)) * width;
    const y = height - (
      ((value - minValue) / range) * height
    );

    return `${x},${y}`;
  }).join(' ');
}

export function FinanceTrendChart({
  entries,
}: {
  entries: FinanceChartEntry[];
}) {
  const actualPoints = buildLinePoints(
    entries.map((entry) => entry.winningsAmount),
    320,
    140,
  );
  const projectedPoints = buildLinePoints(
    entries.map((entry) => entry.projectedWinningsAmount),
    320,
    140,
  );

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

      <div className="finance-line-chart">
        <svg viewBox="0 0 320 140" aria-hidden="true">
          <polyline
            fill="none"
            stroke="var(--finance-actual-color)"
            strokeWidth="3"
            points={actualPoints}
          />
          <polyline
            fill="none"
            stroke="var(--finance-projected-color)"
            strokeWidth="3"
            strokeDasharray="6 6"
            points={projectedPoints}
          />
        </svg>

        <div className="finance-chart-label-row">
          {
            entries.map((entry) => (
              <span key={entry.key}>
                {entry.label}
              </span>
            ))
          }
        </div>
      </div>
    </article>
  );
}

export function FinanceProjectionTimeline({
  entries,
  season,
}: {
  entries: FinanceLeagueSeasonEntry[];
  season: string;
}) {
  const points = buildCurrentFinanceTimeline(entries);
  const actualPoints = buildLinePoints(
    points.map((point) => point.actualAmount ?? 0),
    320,
    140,
  );
  const projectedPoints = buildLinePoints(
    points.map((point) => point.projectedAmount),
    320,
    140,
  );
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
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-actual" />
          Actual payout
        </span>
        <span className="finance-legend-item">
          <i className="finance-legend-line finance-legend-line-projected" />
          Expected payout
        </span>
      </div>

      <div className="finance-line-chart">
        <svg viewBox="0 0 320 140" aria-hidden="true">
          <polyline
            fill="none"
            stroke="var(--finance-actual-color)"
            strokeWidth="3"
            points={actualPoints}
          />
          <polyline
            fill="none"
            stroke="var(--finance-projected-color)"
            strokeWidth="3"
            strokeDasharray="6 6"
            points={projectedPoints}
          />
        </svg>

        <div className="finance-chart-label-row">
          {
            points.map((point) => (
              <span key={point.week}>
                {point.label}
              </span>
            ))
          }
        </div>
      </div>

      <div className="finance-timeline-note">
        <strong>
          {
            latest
              ? formatCurrency(latest.projectedAmount)
              : formatCurrency(0)
          }
        </strong>
        <span>
          Current expected payout snapshot. Weekly snapshots are not
          persisted yet, so this will grow once the sync stores weekly
          finance history.
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
