import { useMemo, useState } from 'react';

import type {
  LeagueDetails,
  LeagueWarPlayerPoint,
} from '@/types';

import './LeagueWarHistoryChart.css';

const POSITIONS = [
  {
    key: 'QB',
    color: '#1f6feb',
  },
  {
    key: 'RB',
    color: '#d97706',
  },
  {
    key: 'WR',
    color: '#059669',
  },
  {
    key: 'TE',
    color: '#c2410c',
  },
] as const;

const WIDTH = 720;
const HEIGHT = 300;
const PADDING = 36;

interface Props {
  league: LeagueDetails;
}

function buildPositionPoints(
  players: LeagueWarPlayerPoint[],
  position: string,
) {
  return players
    .filter((player) => player.position === position)
    .sort((left, right) => left.rank - right.rank);
}

export function LeagueWarSeasonChart({
  league,
}: Props) {
  const [selectedSeason, setSelectedSeason] = useState(
    league.war_player_history[
      league.war_player_history.length - 1
    ]?.season ?? '',
  );

  const selectedHistory = useMemo(
    () => league.war_player_history.find(
      (season) => season.season === selectedSeason,
    ) ?? league.war_player_history[
      league.war_player_history.length - 1
    ],
    [
      league.war_player_history,
      selectedSeason,
    ],
  );

  if (!selectedHistory) {
    return null;
  }

  const maxRank = Math.max(
    ...selectedHistory.players.map((player) => player.rank),
    1,
  );
  const maxWar = Math.max(
    ...selectedHistory.players.map((player) => player.war),
    1,
  );
  const drawableWidth = WIDTH - PADDING * 2;
  const drawableHeight = HEIGHT - PADDING * 2;
  const toX = (rank: number) => (
    PADDING + (
      ((rank - 1) / Math.max(maxRank - 1, 1))
      * drawableWidth
    )
  );
  const toY = (war: number) => (
    HEIGHT - PADDING - (
      (war / maxWar)
      * drawableHeight
    )
  );

  return (
    <section className="league-war-history-card">
      <div className="league-war-history-header">
        <div>
          <p>Analytics</p>
          <h3>Player WAR by position rank</h3>
        </div>

        <label className="league-war-history-select">
          <span>Season</span>
          <select
            value={selectedHistory.season}
            onChange={(event) => {
              setSelectedSeason(event.target.value);
            }}
          >
            {
              league.war_player_history.map((season) => (
                <option
                  key={`${season.season}-${season.source}`}
                  value={season.season}
                >
                  {
                    season.source === 'projection'
                      ? `${season.season} projection`
                      : season.season
                  }
                </option>
              ))
            }
          </select>
        </label>
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
                  backgroundColor: position.color,
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
          aria-label="Player WAR by position rank"
        >
          {
            Array.from({ length: 5 }).map((_, index) => {
              const value = (maxWar / 4) * index;
              const y = toY(value);

              return (
                <g key={index}>
                  <line
                    x1={PADDING}
                    y1={y}
                    x2={WIDTH - PADDING}
                    y2={y}
                    className="league-war-history-grid-line"
                  />
                  <text
                    x={8}
                    y={y + 4}
                    className="league-war-history-axis-label"
                  >
                    {value.toFixed(1)}
                  </text>
                </g>
              );
            })
          }

          {
            POSITIONS.map((position) => {
              const points = buildPositionPoints(
                selectedHistory.players,
                position.key,
              );
              const linePoints = points.map((player) => (
                `${toX(player.rank)},${toY(player.war)}`
              )).join(' ');

              return (
                <g key={position.key}>
                  <polyline
                    fill="none"
                    stroke={position.color}
                    strokeWidth="3"
                    points={linePoints}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  {
                    points.map((player) => (
                      <circle
                        key={player.player_id}
                        cx={toX(player.rank)}
                        cy={toY(player.war)}
                        r="4"
                        fill={position.color}
                      >
                        <title>
                          {`${player.name} (${player.position}${player.rank}) • ${player.war.toFixed(2)} WAR`}
                        </title>
                      </circle>
                    ))
                  }
                </g>
              );
            })
          }

          {
            [1, Math.ceil(maxRank / 2), maxRank].map((rank) => (
              <text
                key={rank}
                x={toX(rank)}
                y={HEIGHT - 8}
                textAnchor="middle"
                className="league-war-history-axis-label"
              >
                {rank}
              </text>
            ))
          }
        </svg>
      </div>
    </section>
  );
}
