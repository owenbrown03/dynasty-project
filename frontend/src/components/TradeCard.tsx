import type { Transaction } from '../types';
import UserCard from './UserCard';

interface Props {
  tx: Transaction;
}

function TradeCard( { tx }: Props) {
  return (
    <div className="trade-card">
      <h4>{tx.league_name}</h4>
      {tx.users.map((user) => (
        <UserCard 
          user={user}
        />
      ))}
    </div>
  );
}

export default TradeCard;