import type { Transaction } from '../../types';
import TradeCard from './TradeCard';
import './TradeCards.css';

interface Props {
  trades: Transaction[];
}

function TradeCards({ trades }: Props) {
  return (
    <div className="trade-cards">
      {trades.map((tx) => (
        <TradeCard 
          tx={tx} 
        />
      ))}
    </div>
  );
}

export default TradeCards;