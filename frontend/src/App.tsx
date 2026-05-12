import { useState } from 'react';
import api from './api/client.ts';
import type { Transaction } from './types/index.ts';
import TradeCards from './components/TradeCards';
import UsernameInput from './components/UsernameInput';

function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState<boolean>(false);

  const handleUserSubmit = async (name: string) => {
    if (!name || name === username) return;

    setLoading(true);
    setUsername(name); 

    try {
      const res = await api.post<Transaction[]>(`/users/${name}/sync`);
      setTransactions(res.data);
    } 
    catch (err) {
      console.error("Fetch failed", err);
    } 
    finally {
      setLoading(false);
    }
  }; 

  return (
    <div className="app-container">
      <h1>
        Dynasty Trade Signals
      </h1>
      <UsernameInput 
        setUsername={handleUserSubmit} 
      />
      {
        loading && <p>Fetching data from Sleeper...</p>
      }
      {!loading && transactions.length > 0 && (
        <TradeCards 
          transactions={transactions} 
        />
      )}
      {!loading && username && transactions.length === 0 && (
        <p>No transactions found for {username}.</p>
      )}
    </div>
  );
}

export default App;