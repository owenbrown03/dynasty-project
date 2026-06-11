import './OrphansPage.css';
import { OrphanCards } from './OrphanCards';
import { useOrphans } from '@/hooks/sleeper/useUsers';

export const OrphansPage = () => {
  const orphans = useOrphans();
  
  return (
    <div className="orphans-container">
      {orphans.loading && <p>Fetching data...</p>}      
      
      {!orphans.loading && Array.isArray(orphans.data) && orphans.data.length > 0 && (
        <OrphanCards orphans={orphans.data} />
      )}
      
      {!orphans.loading && orphans.username && Array.isArray(orphans.data) && orphans.data.length === 0 && (
        <p>No orphans found for "{orphans.username}".</p>
      )}
    </div>
  );
};