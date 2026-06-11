import './RostersPage.css';
import { RosterCards } from './RosterCards';
import { useRosters } from '@/hooks/sleeper/useUsers';

export const RostersPage = () => {
  const rosters = useRosters();
  
  return (
    <div className="rosters-container">
      {rosters.loading && <p>Fetching data...</p>}      
      
      {!rosters.loading && Array.isArray(rosters.data) && rosters.data.length > 0 && (
        <RosterCards rosters={rosters.data} />
      )}
      
      {!rosters.loading && rosters.username && Array.isArray(rosters.data) && rosters.data.length === 0 && (
        <p>No rosters found for "{rosters.username}".</p>
      )}
    </div>
  );
};