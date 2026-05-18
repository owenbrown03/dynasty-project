import './RosterCards.css';
import type { Roster } from '../../types';
import { RosterCard } from './RosterCard';

interface Props {
  rosters: Roster[];
}

export function RosterCards({ rosters }: Props) {
  return (
    <div className="roster-cards">
      {rosters.map((roster) => (
        <RosterCard 
          roster={roster} 
        />
      ))}
    </div>
  );
}