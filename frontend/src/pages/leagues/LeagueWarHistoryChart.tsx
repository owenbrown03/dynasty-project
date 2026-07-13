import type { LeagueDetails } from '@/types';
import { getPositionColor } from '@/utils/positions';

import './LeagueWarHistoryChart.css';

const POSITIONS = [
  {
    key: 'QB',
  },
  {
    key: 'RB',
  },
  {
    key: 'WR',
  },
  {
    key: 'TE',
  },
] as const;

const WIDTH = 680;
const HEIGHT = 240;
const PADDING = 28;

interface Props {
  league: LeagueDetails;
}

export function LeagueWarHistoryChart({
  league,
}: Props) {
  if (!league.war_position_history.length) {
    return null;
  }

  const maxWar = Math.max(
    ...league.war_position_history.flatMap((season) =>
      season.values.map((item) => item.war),
    ),
    1,
  );
  const columnWidth = (
    (WIDTH - PADDING * 2)
    / Math.max(league.war_position_history.length - 1, 1)
  );

  const toY = (war: number) => (
    HEIGHT - PADDING - (
      (war / maxWar)
      * (HEIGHT - PADDING * 2)
    )
  );

  return (
    <section className="league-war-history-card">
      <div className="league-war-history-header">
        <div>
          <p>WAR history</p>
          <h3>Year-over-year position WAR</h3>
        </div>
        <span>
          Historical regular seasons plus current projection
        </span>
      </div>

      <div className="league-war-history-legend">
        {
          POSITIONS.map((position) => (
            <div
              key={position.key}
              className="league-war-history-legend-item"
            >
              <span
                className="league-war-history-swatch"
                style={{
                  backgroundColor: getPositionColor(position.key),
                }}
              />
              <strong>{position.key}</strong>
            </div>
          ))
        }
      </div>

      <div className="league-war-history-scroll">
        <svg
          className="league-war-history-svg"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-label="Year-over-year WAR by position"
        >
          {
            league.war_position_history.map((season, index) => {
              const x = PADDING + index * columnWidth;
              return (
                <g key={season.season}>
                  <line
                    x1={x}
                    y1={PADDING}
                    x2={x}
                    y2={HEIGHT - PADDING}
                    className="league-war-history-grid-line"
                  />
                  <text
                    x={x}
                    y={HEIGHT - 6}
                    textAnchor="middle"
                    className="league-war-history-axis-label"
                  >
                    {season.source === 'projection' ? `${season.season}P` : season.season}
                  </text>
                </g>
              );
            })
          }

          {
            POSITIONS.map((position) => {
              const color = getPositionColor(position.key);
              const points = league.war_position_history.map((season, index) => {
                const value = season.values.find(
                  (item) => item.position === position.key,
                )?.war ?? 0;
                return `${PADDING + index * columnWidth},${toY(value)}`;
              }).join(' ');

              return (
                <g key={position.key}>
                  <polyline
                    fill="none"
                    stroke={color}
                    strokeWidth="3"
                    points={points}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  {
                    league.war_position_history.map((season, index) => {
                      const value = season.values.find(
                        (item) => item.position === position.key,
                      )?.war ?? 0;
                      const x = PADDING + index * columnWidth;
                      const y = toY(value);

                      return (
                        <g key={`${position.key}-${season.season}`}>
                          <circle
                            cx={x}
                            cy={y}
                            r="5"
                            fill={color}
                          />
                          <text
                            x={x}
                            y={y - 10}
                            textAnchor="middle"
                            className="league-war-history-point-label"
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
