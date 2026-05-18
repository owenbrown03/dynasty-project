import './TradeCards.css';
import type { Transaction } from '../../types';
import { TradeCard } from './TradeCard';

interface Props {
  trades: Transaction[];
}

export function TradeCards({ trades }: Props) {
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