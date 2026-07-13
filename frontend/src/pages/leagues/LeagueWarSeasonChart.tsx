import { useMemo, useState } from 'react';

import type {
  LeagueDetails,
  LeagueWarPlayerPoint,
} from '@/types';
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

const WIDTH = 720;
const HEIGHT = 300;
const PADDING = 36;
const Y_AXIS_TICK_COUNT = 5;

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
  const [selectedWarType, setSelectedWarType] = useState<
    'starter' | 'roster'
  >('roster');
  const [hoveredPlayer, setHoveredPlayer] = useState<{
    color: string;
    label: string;
    war: number;
    x: number;
    y: number;
  } | null>(null);
  const [selectedSeason, setSelectedSeason] = useState(
    league.war_player_history.find(
      (season) => season.war_type === 'roster'
        && season.source === 'projection',
    )?.season
      ?? league.war_player_history.find(
        (season) => season.war_type === 'roster',
      )?.season
      ?? '',
  );
  const availableSeasons = useMemo(
    () => league.war_player_history.filter(
      (season) => season.war_type === selectedWarType,
    ),
    [
      league.war_player_history,
      selectedWarType,
    ],
  );

  const selectedHistory = useMemo(
    () => availableSeasons.find(
      (season) => season.season === selectedSeason,
    ) ?? availableSeasons[
      availableSeasons.length - 1
    ],
    [
      availableSeasons,
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
  const minWar = Math.min(
    ...selectedHistory.players.map((player) => player.war),
    0,
  );
  const maxWar = Math.max(
    ...selectedHistory.players.map((player) => player.war),
    0,
  );
  const drawableWidth = WIDTH - PADDING * 2;
  const drawableHeight = HEIGHT - PADDING * 2;
  const warRange = Math.max(
    maxWar - minWar,
    1,
  );
  const yAxisValues = Array.from(
    {
      length: Y_AXIS_TICK_COUNT,
    },
    (_, index) => (
      minWar + (
        (warRange / Math.max(Y_AXIS_TICK_COUNT - 1, 1))
        * index
      )
    ),
  );
  const toX = (rank: number) => (
    PADDING + (
      ((rank - 1) / Math.max(maxRank - 1, 1))
      * drawableWidth
    )
  );
  const toY = (war: number) => (
    HEIGHT - PADDING - (
      ((war - minWar) / warRange)
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
          <span>WAR type</span>
          <select
            value={selectedWarType}
            onChange={(event) => {
              const nextWarType = event.target.value as 'starter' | 'roster';
              setHoveredPlayer(null);
              setSelectedWarType(nextWarType);
              setSelectedSeason(
                league.war_player_history.find(
                  (season) => season.war_type === nextWarType
                    && season.source === 'projection',
                )?.season
                  ?? league.war_player_history.find(
                    (season) => season.war_type === nextWarType,
                  )?.season
                  ?? '',
              );
            }}
          >
            <option value="roster">Roster WAR</option>
            <option value="starter">Starter WAR</option>
          </select>
        </label>

        <label className="league-war-history-select">
          <span>Season</span>
          <select
            value={selectedHistory.season}
            onChange={(event) => {
              setHoveredPlayer(null);
              setSelectedSeason(event.target.value);
            }}
          >
            {
              availableSeasons.map((season) => (
                <option
                  key={`${season.season}-${season.source}-${season.war_type}`}
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
          aria-label="Player WAR by position rank"
        >
          {
            yAxisValues.map((value) => {
              const y = toY(value);

              return (
                <g key={value}>
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
              const color = getPositionColor(position.key);
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
                    stroke={color}
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
                        fill={color}
                        className="league-war-history-point"
                        onMouseEnter={() => {
                          setHoveredPlayer({
                            color,
                            label: `${player.name} (${player.position}${player.rank})`,
                            war: player.war,
                            x: toX(player.rank),
                            y: toY(player.war),
                          });
                        }}
                        onMouseLeave={() => {
                          setHoveredPlayer((current) => (
                            current?.label === `${player.name} (${player.position}${player.rank})`
                              ? null
                              : current
                          ));
                        }}
                      />
                    ))
                  }
                </g>
              );
            })
          }

          {
            hoveredPlayer
              ? (
                <g
                  className="league-war-history-tooltip"
                  transform={`translate(${Math.min(
                    hoveredPlayer.x + 10,
                    WIDTH - 220,
                  )} ${Math.max(hoveredPlayer.y - 48, 12)})`}
                >
                  <rect
                    width={200}
                    height={40}
                    rx={6}
                    fill="var(--color-surface-raised)"
                    stroke={hoveredPlayer.color}
                  />
                  <text
                    x={10}
                    y={17}
                    className="league-war-history-tooltip-label"
                  >
                    {hoveredPlayer.label}
                  </text>
                  <text
                    x={10}
                    y={31}
                    className="league-war-history-tooltip-value"
                  >
                    {`${hoveredPlayer.war.toFixed(2)} WAR`}
                  </text>
                </g>
              )
              : null
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
