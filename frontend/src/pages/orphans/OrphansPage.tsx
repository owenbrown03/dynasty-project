import './OrphansPage.css';
import { LoadingState } from '@/components/feedback/LoadingState';
import { OrphanCards } from './OrphanCards';
import { useOrphans } from '@/hooks/sleeper/useUsers';

export const OrphansPage = () => {
  const orphans = useOrphans();

  return (
    <div className="orphans-container">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Orphans</p>
          <h1 className="page-title">Available orphan rosters</h1>
          <p className="page-description">
            Review league orphan teams and scan player cores before deciding
            where to dig deeper.
          </p>
        </div>
      </section>

      {orphans.loading && (
        <div className="orphans-empty-state">
          <LoadingState label="Fetching orphan rosters..." />
        </div>
      )}

      {!orphans.loading && Array.isArray(orphans.data) && orphans.data.length > 0 && (
        <OrphanCards orphans={orphans.data} />
      )}

      {!orphans.loading && orphans.username && Array.isArray(orphans.data) && orphans.data.length === 0 && (
        <div className="orphans-empty-state">
          <p>No orphans found for "{orphans.username}".</p>
        </div>
      )}
    </div>
  );
};
