import type { Transaction } from '../types';
import TradeCard from './TradeCard';
import './TradeCards.css';

interface Props {
  transactions: Transaction[];
}

function TradeCards({ transactions }: Props) {
  return (
    <div className="trade-cards">
      {transactions.map((tx) => (
        <TradeCard 
          tx={tx} 
        />
      ))}
    </div>
  );
}

export default TradeCards;