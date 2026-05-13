import './Rosters.css';
import RosterCards from './RosterCards';
import { rosterLoader } from '../../hooks/usernameHandler';

const Rosters = ({ username }) => {
  const { rosters, loading } = rosterLoader(username);
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

export default Rosters;