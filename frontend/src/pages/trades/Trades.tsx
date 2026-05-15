import './Trades.css';
import TradeCards from './TradeCards';
import { useRouteUsername, useTradeLoader } from '../../hooks/usernameHandler';

const Trades = () => {
  const username = useRouteUsername();
  const { trades, loading } = useTradeLoader(username);
  return (
    <div className="trades-container">
      {loading && <p>Fetching data...</p>}
      {!loading && trades.length > 0 && <TradeCards trades={trades} />}
      {!loading && username && trades.length === 0 && <p>No results.</p>}
    </div>
  );
};

export default Trades;
