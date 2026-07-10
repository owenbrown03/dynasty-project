import './RosterCard.css';
import type { LeagueRoster } from '@/types';
import { PlayerTable } from './PlayerTable';

interface Props {
  roster: LeagueRoster;
}

export function RosterCard({ roster }: Props) {
  return (
    <div className="roster-card">
      <header className="roster-header">
        <div className="roster-header-main">
          <p className="roster-header-kicker">Roster</p>
          <h3 className="roster-title">Rank #{roster.rank}</h3>
        </div>

        <div className="roster-war-stat">
          <span>Roster WAR</span>
          <strong>{roster.total_roster_war.toFixed(2)}</strong>
        </div>
      </header>

      <PlayerTable players={roster.players} />
    </div>
  );
}
