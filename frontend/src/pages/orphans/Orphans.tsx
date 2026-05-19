import './Orphans.css';
import { OrphanCards } from './OrphanCards';
import { useOrphanLoader } from '../../hooks/usernameHandler';
import { useUserContext } from '../../context/UserContext';

export const Orphans = () => {
  const { username } = useUserContext();
  const { orphans, loading } = useOrphanLoader(username);
  
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