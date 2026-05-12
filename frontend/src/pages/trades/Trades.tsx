import './Trades.css';
import TradeCards from './TradeCards';

const Trades = ({ transactions, username, loading }) => (
  <>
    {!loading && transactions.length > 0 && <TradeCards transactions={transactions} />}
    {!loading && username && transactions.length === 0 && <p>No results.</p>}
  </>
);

export default Trades;