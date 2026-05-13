import type { Roster } from '../../types';
import RosterCard from './RosterCard';
import './RosterCards.css';

interface Props {
  rosters: Roster[];
}

function RosterCards({ rosters }: Props) {
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

export default RosterCards;