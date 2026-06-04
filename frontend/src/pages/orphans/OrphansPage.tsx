import './OrphansPage.css';
import { OrphanCards } from './OrphanCards';
import { useUserContext } from '../../context/SleeperContext';
import { useQuery } from '@/hooks/useQuery';
import { api } from '@/api/v1/endpoints';
import { type Orphan } from '@/types/index'

export const OrphansPage = () => {
  const { username } = useUserContext();
  const { data: orphans, loading } = useQuery<Orphan[]>(
    `orphan-${username}`, 
    () => api.users.getOrphans(username!),
    [username]
  );
  
  return (
    <div className="orphans-container">
      {loading && <p>Fetching data...</p>}      
  
      {!loading && orphans && orphans.length > 0 && (
        <OrphanCards orphans={orphans} />
      )}
  
      {!loading && username && orphans && orphans.length === 0 && (
        <p>No orphans found for "{username}".</p>
      )}
    </div>
  );
};