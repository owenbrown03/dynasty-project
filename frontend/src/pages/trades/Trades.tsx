import './Trades.css';
import { TradeCards } from './TradeCards';
import { useTradeLoader } from '../../hooks/usernameHandler';
import { useUserContext } from '../../context/UserContext';

export const Trades = () => {
  const { username } = useUserContext();
  const { trades, loading } = useTradeLoader(username);

  if (loading) {
    return (
      <div className="trades-container">
        <p className="loading-text">Fetching data...</p>
      </div>
    );
  }

  if (trades.length > 0) {
    return (
      <div className="trades-container">
        <TradeCards trades={trades} />
      </div>
    );
  }

  return (
    <div className="trades-container">
      {username ? (
        <p className="no-results-text">No transaction history found for {username}.</p>
      ) : (
        <p className="no-results-text">Please enter a username to search trades.</p>
      )}
    </div>
  );
};