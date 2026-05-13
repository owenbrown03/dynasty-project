import './Trades.css';
import TradeCards from './TradeCards';
import { tradeLoader } from '../../hooks/usernameHandler';

const Trades = ({ username }) => {
  const { trades, loading } = tradeLoader(username);
  return (
    <div className="trades-container">
      {loading && <p>Fetching data...</p>}
      {!loading && trades.length > 0 && <TradeCards trades={trades} />}
      {!loading && username && trades.length === 0 && <p>No results.</p>}
    </div>
  );
};

export default Trades;