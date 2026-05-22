import './RostersPage.css';
import { RosterCards } from './RosterCards';
import { useUserContext } from '../../context/UserContext';
import { useQuery } from '@/hooks/useQuery';
import { api } from '@/api/v1/endpoints';
import { type Roster } from '@/types/index'

export const RostersPage = () => {
  const { username } = useUserContext();
  const { data: rosters, loading } = useQuery<Roster[]>(
    `rosters-${username}`, 
    () => api.users.getRosters(username!),
    [username]
  );
  
  return (
    <div className="rosters-container">
      {loading && <p>Fetching data...</p>}      
      
      {!loading && Array.isArray(rosters) && rosters.length > 0 && (
        <RosterCards rosters={rosters} />
      )}
      
      {!loading && username && Array.isArray(rosters) && rosters.length === 0 && (
        <p>No rosters found for "{username}".</p>
      )}
    </div>
  );
};