import type { Transaction } from '../../types';
import UserCard from './UserCard';
import './TradeCard.css';

interface Props {
  tx: Transaction;
}

function TradeCard({ tx }: Props) {
  return (
    <div className="trade-card">
      <header className="league-header">{tx.league_name}</header>      
      <div className="trade-users-row">
        {tx.users.map((user, index) => (
          <UserCard 
            key={`${tx.transaction_id}-${index}`}
            user={user} 
          />
        ))}
      </div>
    </div>
  );
}

export default TradeCard;