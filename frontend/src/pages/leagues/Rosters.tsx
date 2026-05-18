import { useParams } from 'react-router';

import './Rosters.css';
import { RosterCards } from './RosterCards';
import { useRosterLoader } from '../../hooks/usernameHandler';

export const Rosters = () => {
  const { username } = useParams<{ username: string }>();
  const { rosters, loading } = useRosterLoader(username);
  
  return (
<div className="rosters-container">
      {loading && <p>Fetching data...</p>}      
      {!loading && rosters && rosters.length > 0 && (
        <RosterCards rosters={rosters} />
      )}
      {!loading && username && rosters && rosters.length === 0 && (
        <p>No rosters found for "{username}".</p>
      )}
    </div>
  );
};