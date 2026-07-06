import { TradeCards } from './TradeCards';
import { useTrades } from '@/hooks/sleeper/useTrades';

export const TradeResearchTab = () => {
  const trades = useTrades();

  if (trades.fetching) {
    return (
      <div className="trades-container">
        <p className="loading-text">Fetching trade signals...</p>
      </div>
    );
  }

  if (Array.isArray(trades.data) && trades.data.length > 0) {
    return (
      <div className="trades-container">
        <TradeCards trades={trades.data} />
      </div>
    );
  }

  return (
    <div className="trades-container">
      {trades.username ? (
        <p className="no-results-text">No transaction history found for "{trades.username}".</p>
      ) : (
        <p className="no-results-text">Please enter a username to search trades.</p>
      )}
    </div>
  );
};