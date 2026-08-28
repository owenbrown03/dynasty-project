import { useMemo, useState } from 'react';
import { useBootstrap } from '@/hooks/useBootstrap';
import { UserAvatar } from '@/components/users/UserAvatar';
import type { LeagueDetails } from '@/types';
import {
  computeRosterStatSummary,
  formatRosterStatValue,
  getRosterStatValue,
  ROSTER_STAT_OPTIONS,
  type RosterStatKey,
  sortRostersByStat,
} from './rosterChart';

import './LeagueRosterBarChart.css';

interface Props {
  league: LeagueDetails;
}

export function LeagueRosterBarChart({ league }: Props) {
  const bootstrap = useBootstrap();
  const currentUserId = bootstrap.data?.sleeper?.sleeper_user_id ?? null;

  const [selectedStat, setSelectedStat] =
    useState<RosterStatKey>('dynasty_roster_war');
  const [sortDirection, setSortDirection] =
    useState<'desc' | 'asc'>('desc');

  const sortedRosters = useMemo(
    () => sortRostersByStat(league.rosters, selectedStat, sortDirection),
    [league.rosters, selectedStat, sortDirection],
  );

  const selectedOption = useMemo(
    () =>
      ROSTER_STAT_OPTIONS.find((option) => option.key === selectedStat)
      ?? ROSTER_STAT_OPTIONS[0],
    [selectedStat],
  );

  const summary = useMemo(
    () =>
      computeRosterStatSummary(
        league,
        sortedRosters,
        selectedStat,
        currentUserId,
      ),
    [league, sortedRosters, selectedStat, currentUserId],
  );

  const maxVal = useMemo(() => {
    const vals = league.rosters
      .map((r) => getRosterStatValue(r, selectedStat))
      .filter((v): v is number => v !== null);
    return Math.max(...vals, 0.0001);
  }, [league.rosters, selectedStat]);

  const groupedOptions = useMemo(() => {
    const groups: Record<string, typeof ROSTER_STAT_OPTIONS> = {};
    for (const opt of ROSTER_STAT_OPTIONS) {
      if (!groups[opt.group]) {
        groups[opt.group] = [];
      }
      groups[opt.group].push(opt);
    }
    return groups;
  }, []);

  return (
    <section
      className="league-roster-bar-chart-card"
      aria-label="League roster bar chart"
    >
      <header className="league-roster-bar-chart-header">
        <div className="league-roster-bar-chart-title-wrap">
          <p className="league-roster-bar-chart-kicker">Bar Chart View</p>
          <h2 className="league-roster-bar-chart-title">
            {selectedOption.shortLabel} by Roster
          </h2>
          <p className="league-roster-bar-chart-subtitle">
            Comparing all {league.total_rosters} rosters sorted by{' '}
            {selectedOption.label.toLowerCase()}{' '}
            ({sortDirection === 'desc' ? 'highest to lowest' : 'lowest to highest'}).
          </p>
        </div>

        <div className="league-roster-bar-chart-controls">
          <label className="league-roster-bar-chart-select-label">
            <span>Metric</span>
            <select
              aria-label="Select stat metric"
              value={selectedStat}
              onChange={(e) =>
                setSelectedStat(e.target.value as RosterStatKey)
              }
              className="league-roster-bar-chart-select"
            >
              {Object.entries(groupedOptions).map(([groupName, opts]) => (
                <optgroup key={groupName} label={groupName}>
                  {opts.map((opt) => (
                    <option key={opt.key} value={opt.key}>
                      {opt.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>

          <label className="league-roster-bar-chart-select-label">
            <span>Sort Order</span>
            <select
              aria-label="Select sort order"
              value={sortDirection}
              onChange={(e) =>
                setSortDirection(e.target.value as 'desc' | 'asc')
              }
              className="league-roster-bar-chart-select"
            >
              <option value="desc">Highest First</option>
              <option value="asc">Lowest First</option>
            </select>
          </label>
        </div>
      </header>

      {summary.max !== null && (
        <div className="league-roster-bar-chart-summary">
          <div className="league-roster-bar-chart-summary-item">
            <span>Leader / Top</span>
            <strong>{formatRosterStatValue(summary.max, selectedStat)}</strong>
          </div>
          <div className="league-roster-bar-chart-summary-item">
            <span>League Avg</span>
            <strong>{formatRosterStatValue(summary.avg, selectedStat)}</strong>
          </div>
          <div className="league-roster-bar-chart-summary-item">
            <span>Lowest</span>
            <strong>{formatRosterStatValue(summary.min, selectedStat)}</strong>
          </div>
          {summary.userRank !== null && summary.userValue !== null && (
            <div className="league-roster-bar-chart-summary-item is-user-summary">
              <span>Your Team</span>
              <strong>
                #{summary.userRank} · {formatRosterStatValue(summary.userValue, selectedStat)}
              </strong>
            </div>
          )}
        </div>
      )}

      <div className="league-roster-bar-chart-legend">
        <div className="league-roster-bar-chart-legend-item">
          <span className="league-roster-bar-chart-swatch standard-swatch" />
          <span>League Team</span>
        </div>
        {currentUserId && (
          <div className="league-roster-bar-chart-legend-item">
            <span className="league-roster-bar-chart-swatch user-swatch" />
            <span>Your Team (Highlighted)</span>
          </div>
        )}
      </div>

      <div
        className="league-roster-bar-chart-list"
        role="list"
        aria-label="Roster bar chart rankings"
      >
        {sortedRosters.map((roster, index) => {
          const rawValue = getRosterStatValue(roster, selectedStat);
          const isUser = Boolean(
            currentUserId
            && roster.owner?.user_id
            && roster.owner.user_id === currentUserId,
          );
          const rank = index + 1;
          const pct = rawValue !== null && rawValue > 0
            ? Math.min(100, Math.max(2, (rawValue / maxVal) * 100))
            : 0;
          const formattedVal = formatRosterStatValue(rawValue, selectedStat);

          return (
            <div
              key={roster.roster_id}
              role="listitem"
              className={`league-roster-bar-row${isUser ? ' is-user-team' : ''}`}
            >
              <div className="league-roster-bar-identity">
                <span className="league-roster-bar-rank">#{rank}</span>
                <UserAvatar
                  avatarId={roster.owner?.avatar}
                  name={roster.owner?.display_name || `Team ${roster.roster_id}`}
                  size="sm"
                />
                <div className="league-roster-bar-names">
                  <span className="league-roster-bar-team-name">
                    {roster.owner?.display_name || `Team ${roster.roster_id}`}
                  </span>
                  {isUser && (
                    <span className="league-roster-bar-user-badge">You</span>
                  )}
                </div>
              </div>

              <div className="league-roster-bar-track-wrap">
                <div className="league-roster-bar-track">
                  <div
                    className={`league-roster-bar-fill${isUser ? ' is-user-bar' : ''}`}
                    style={{ width: `${pct}%` }}
                    aria-valuenow={rawValue ?? 0}
                    aria-valuemin={0}
                    aria-valuemax={maxVal}
                  />
                </div>
              </div>

              <div className="league-roster-bar-value-wrap">
                <strong className="league-roster-bar-value">
                  {formattedVal}
                </strong>
                <span className="league-roster-bar-subvalue">
                  {roster.record ? `${roster.record} record` : `Roster #${roster.roster_id}`}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
