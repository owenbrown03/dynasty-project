import './TradesPage.css';
import { TradeCards } from './TradeCards';
import { useUserContext } from '../../context/UserContext';
import { useQuery } from '@/hooks/useQuery';
import { api } from '@/api/v1/endpoints';
import { type Transaction } from '@/types/index';

export const TradesPage = () => {
  const { username } = useUserContext();
  
  const { data: trades, loading } = useQuery<Transaction[]>(
    `trades-${username}`, 
    () => api.trades.getTradeSignals(username!), 
    [username]
  );

  if (loading) {
    return (
      <div className="trades-container">
        <p className="loading-text">Fetching trade signals...</p>
      </div>
    );
  }

  if (Array.isArray(trades) && trades.length > 0) {
    return (
      <div className="trades-container">
        <TradeCards trades={trades} />
      </div>
    );
  }

  return (
    <div className="trades-container">
      {username ? (
        <p className="no-results-text">No transaction history found for "{username}".</p>
      ) : (
        <p className="no-results-text">Please enter a username to search trades.</p>
      )}
    </div>
  );
};