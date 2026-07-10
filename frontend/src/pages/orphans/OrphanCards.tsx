import './OrphanCards.css';
import type { Orphan } from '../../types';
import { OrphanCard } from './OrphanCard';

interface Props {
  orphans: Orphan[];
}

export function OrphanCards({ orphans }: Props) {
  return (
    <div className="orphan-cards">
      {orphans.map((orphan) => (
        <OrphanCard 
          key={`${orphan.league_name}-${orphan.roster_name}`}
          orphan={orphan} 
        />
      ))}
    </div>
  );
}
