import './LeagueCard.css';

import { useEffect, useState } from 'react';

import { LeagueAvatar } from '@/components/leagues/LeagueAvatar';
import { useSaveUserNote } from '@/hooks/sleeper/useLeagues';
import type { LeagueDetails } from '@/types';
import { notify } from '@/utils/notify';
import { RosterCard } from './RosterCard';


interface Props {
  league: LeagueDetails;
}


export function LeagueCard({
  league,
}: Props) {
  const { saveNote, saving: savingNote } = useSaveUserNote();
  const [note, setNote] = useState(league.note);

  useEffect(() => {
    setNote(league.note);
  }, [league.note]);

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

  return (
    <div className="league-card">
      <header className="league-header">
        <div className="league-header-identity">
          <LeagueAvatar
            avatarId={league.avatar}
            name={league.league_name}
            size="lg"
          />

          <div>
            <p className="league-header-kicker">League</p>
            <h2 className="league-title">{league.league_name}</h2>
            <p className="league-subtitle">
              {league.season} · {league.total_rosters} teams
            </p>
          </div>
        </div>

        <div className="league-summary-stat">
          <strong>{league.rosters.length}</strong>
          <small>rosters</small>
        </div>
      </header>

      <div className="league-badge-row">
        {
          league.settings_badges.map((badge) => (
            <span
              key={`${league.league_id}-${badge}`}
              className="league-badge"
            >
              {badge}
            </span>
          ))
        }
      </div>

      <section className="league-settings-panel">
        <div className="league-settings-header">
          <p>League settings</p>
        </div>

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
        {league.rosters.map((roster) => (
          <RosterCard
            key={roster.roster_id}
            roster={roster}
            draftPickProjectionSummary={league.draft_pick_projection_summary}
          />
        ))}
      </div>
    </div>
  );
}
