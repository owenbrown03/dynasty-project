import './LeagueCard.css';

import { useEffect, useMemo, useState } from 'react';

import { LeagueAvatar } from '@/components/leagues/LeagueAvatar';
import { useBootstrap } from '@/hooks/useBootstrap';
import { useSaveUserNote } from '@/hooks/sleeper/useLeagues';
import type {
  LeagueDetails,
  LeagueRoster,
  ValueBasis,
  WarValueSettings,
} from '@/types';
import { notify } from '@/utils/notify';
import { getValueBasisLabel } from '@/utils/valueBasis';
import { RosterCard } from './RosterCard';


interface Props {
  league: LeagueDetails;
  rosterSortBasis: ValueBasis;
  warValueSettings: WarValueSettings;
}

function getVisibleLeagueValueBasis(
  valueBasis: ValueBasis,
): ValueBasis {
  if (
    valueBasis === 'dynasty_starter_war'
    || valueBasis === 'dynasty_roster_war'
    || valueBasis === 'redraft_starter_war'
    || valueBasis === 'redraft_roster_war'
  ) {
    return 'sleeper_war';
  }

  if (valueBasis === 'adp') {
    return 'ktc';
  }

  return valueBasis;
}

function getRosterWarTotal(
  roster: LeagueRoster,
  {
    timeframe,
    scope,
  }: {
    timeframe: 'redraft' | 'dynasty';
    scope: 'starter' | 'roster';
  },
): number {
  if (timeframe === 'redraft') {
    return scope === 'starter'
      ? roster.total_redraft_starter_war
      : roster.total_redraft_roster_war;
  }

  return scope === 'starter'
    ? roster.total_dynasty_starter_war
    : roster.total_dynasty_roster_war;
}

function getRosterMyWarTotal(
  roster: LeagueRoster,
  {
    timeframe,
    scope,
  }: {
    timeframe: 'redraft' | 'dynasty';
    scope: 'starter' | 'roster';
  },
): number {
  const metricName = (
    timeframe === 'redraft'
      ? (
        scope === 'starter'
          ? 'my_redraft_starter_war'
          : 'my_redraft_roster_war'
      )
      : (
        scope === 'starter'
          ? 'my_dynasty_starter_war'
          : 'my_dynasty_roster_war'
      )
  );

  return roster.players.reduce(
    (total, player) => (
      total
      + (
        player[metricName]
        ?? 0
      )
    ),
    0,
  );
}

function getRosterSortValue(
  roster: LeagueRoster,
  {
    valueBasis,
    warValueSettings,
  }: {
    valueBasis: ValueBasis;
    warValueSettings: WarValueSettings;
  },
): number {
  const visibleValueBasis = getVisibleLeagueValueBasis(
    valueBasis,
  );

  switch (visibleValueBasis) {
    case 'fantasycalc':
      return roster.total_asset_fc_value;
    case 'sleeper_war':
      return getRosterWarTotal(
        roster,
        warValueSettings.sleeper_projection,
      );
    case 'my_war':
      return getRosterMyWarTotal(
        roster,
        warValueSettings.my,
      );
    case 'ktc':
    default:
      return roster.total_asset_ktc_value;
  }
}


export function LeagueCard({
  league,
  rosterSortBasis,
  warValueSettings,
}: Props) {
  const { saveNote, saving: savingNote } = useSaveUserNote();
  const [note, setNote] = useState(league.note);

  useEffect(() => {
    setNote(league.note);
  }, [league.note]);

  const sortedRosters = useMemo(
    () => (
      [...league.rosters].sort((left, right) => {
        if (left.rank !== right.rank) {
          return left.rank - right.rank;
        }

        const leftValue = getRosterSortValue(
          left,
          {
            valueBasis: rosterSortBasis,
            warValueSettings,
          },
        );
        const rightValue = getRosterSortValue(
          right,
          {
            valueBasis: rosterSortBasis,
            warValueSettings,
          },
        );

        if (rightValue !== leftValue) {
          return rightValue - leftValue;
        }

        return left.roster_id - right.roster_id;
      })
    ),
    [
      league.rosters,
      rosterSortBasis,
      warValueSettings,
    ],
  );

  const handleSaveNote = async () => {
    try {
      await saveNote({
        league_id: league.league_id,
        note,
      });
      notify.success('League note saved.');
    } catch {
      notify.error('Unable to save league note.');
    }
  };

  const bootstrap = useBootstrap();
  const currentUserId = bootstrap.data?.sleeper?.sleeper_user_id;
  const currentUsername = bootstrap.data?.sleeper?.sleeper_username?.toLowerCase();

  return (
    <div className="league-card">
      <header className="league-header">
        <div className="league-header-identity">
          <LeagueAvatar
            avatarId={league.avatar}
            name={league.league_name}
            size="md"
          />

          <div>
            <p className="league-header-kicker">League</p>
            <h2 className="league-title">{league.league_name}</h2>
            <p className="league-subtitle">
              {league.season} · {league.total_rosters} teams · ordered by current standings · value ranks by {getValueBasisLabel(rosterSortBasis)}
            </p>
          </div>
        </div>
      </header>

      <section className="league-settings-panel league-overview-panel">
        <div className="league-settings-header">
          <p>League overview</p>
        </div>

        <div className="league-overview-content">
          <div className="league-settings-grid">
            {
              league.settings_details.map((detail) => (
                <div
                  key={`${league.league_id}-${detail.label}`}
                  className="league-settings-item"
                >
                  <span>{detail.label}</span>
                  <strong>{detail.value}</strong>
                </div>
              ))
            }
          </div>
        </div>
      </section>

      <section className="league-detail-section">
        <div className="league-detail-header">
          <p>League notes</p>
        </div>

        <div className="league-note-editor">
          <textarea
            value={note}
            onChange={(event) => {
              setNote(event.target.value);
            }}
            placeholder="Add your roster build plan, position needs, and future pick strategy..."
          />

          <button
            type="button"
            className="button-secondary"
            disabled={savingNote}
            onClick={() => {
              void handleSaveNote();
            }}
          >
            {
              savingNote
                ? 'Saving...'
                : 'Save notes'
            }
          </button>
        </div>
      </section>

      <div className="rosters">
        {sortedRosters.map((roster) => {
          const isUserRoster = !!(
            (currentUserId && roster.owner?.user_id === currentUserId) ||
            (currentUsername && roster.owner?.display_name?.toLowerCase() === currentUsername)
          );

          return (
            <RosterCard
              key={roster.roster_id}
              roster={roster}
              displayRank={roster.rank}
              rosterConstructionTargets={league.roster_construction_targets}
              draftPickProjectionSummary={league.draft_pick_projection_summary}
              valueBasis={rosterSortBasis}
              warValueSettings={warValueSettings}
              isCheap={!!league.is_cheap_data}
              leagueId={league.league_id}
              isUserRoster={isUserRoster}
            />
          );
        })}
      </div>
    </div>
  );
}
