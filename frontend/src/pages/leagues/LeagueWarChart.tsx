import type { LeagueDetails } from '@/types';

import './LeagueWarChart.css';

import {
  buildLeaguePositionWarSeries,
  WAR_CHART_METRICS,
} from './warChart';

interface Props {
  league: LeagueDetails;
}

const CHART_HEIGHT = 220;
const CHART_WIDTH = 680;
const CHART_PADDING = 28;

export function LeagueWarChart({
  league,
}: Props) {
  const series = buildLeaguePositionWarSeries(
    league,
  );
  const values = series.flatMap((item) => item.values);
  const maxValue = Math.max(
    ...values,
    1,
  );
  const drawableHeight = (
    CHART_HEIGHT - CHART_PADDING * 2
  );
  const columnWidth = (
    (CHART_WIDTH - CHART_PADDING * 2)
    / Math.max(WAR_CHART_METRICS.length - 1, 1)
  );

  const toY = (value: number) => (
    CHART_HEIGHT - CHART_PADDING - (
      (value / maxValue) * drawableHeight
    )
  );

  return (
    <section className="league-war-chart-card">
      <div className="league-war-chart-header">
        <div>
          <p>WAR by position</p>
          <h3>Current league WAR snapshot</h3>
        </div>

        <span>
          Current synced projection season only
        </span>
      </div>

      <div className="league-war-chart-legend">
        {
          series.map((item) => (
            <div
              key={item.position}
              className="league-war-chart-legend-item"
            >
              <span
                className="league-war-chart-swatch"
                style={{
                  backgroundColor: item.color,
                }}
              />
              <strong>{item.position}</strong>
              <small>
                {
                  item.values[
                    item.values.length - 1
                  ].toFixed(2)
                }
                {' '}
                dynasty roster WAR
              </small>
            </div>
          ))
        }
      </div>

      <div className="league-war-chart-scroll">
        <svg
          className="league-war-chart-svg"
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          role="img"
          aria-label="League WAR by position chart"
        >
          {
            WAR_CHART_METRICS.map((metric, index) => {
              const x = CHART_PADDING + index * columnWidth;

              return (
                <g key={metric.key}>
                  <line
                    x1={x}
                    y1={CHART_PADDING}
                    x2={x}
                    y2={CHART_HEIGHT - CHART_PADDING}
                    className="league-war-chart-grid-line"
                  />
                  <text
                    x={x}
                    y={CHART_HEIGHT - 6}
                    textAnchor="middle"
                    className="league-war-chart-axis-label"
                  >
                    {metric.label}
                  </text>
                </g>
              );
            })
          }

          {
            series.map((item) => {
              const points = item.values.map((value, index) => {
                const x = CHART_PADDING + index * columnWidth;
                const y = toY(value);
                return `${x},${y}`;
              }).join(' ');

              return (
                <g key={item.position}>
                  <polyline
                    fill="none"
                    stroke={item.color}
                    strokeWidth="3"
                    points={points}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  {
                    item.values.map((value, index) => {
                      const x = CHART_PADDING + index * columnWidth;
                      const y = toY(value);

                      return (
                        <g key={`${item.position}-${index}`}>
                          <circle
                            cx={x}
                            cy={y}
                            r="5"
                            fill={item.color}
                          />
                          <text
                            x={x}
                            y={y - 10}
                            textAnchor="middle"
                            className="league-war-chart-point-label"
                          >
                            {value.toFixed(1)}
                          </text>
                        </g>
                      );
                    })
                  }
                </g>
              );
            })
          }
        </svg>
      </div>
    </section>
  );
}
