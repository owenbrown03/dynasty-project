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
        <span>Rank #{roster.rank}</span>
        <span>WAR: {roster.total_roster_war.toFixed(2)}</span>
      </header>

      <PlayerTable players={roster.players} />
    </div>
  );
}