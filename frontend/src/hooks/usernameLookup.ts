import { useState } from 'react';
import api from '../api/client.ts';
import type { Transaction } from '../types/index.ts';

function usernameLookup() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState('');

  const handleUserSubmit = async (name: string) => {
    if (!name || name === username) return;
    setUsername(name);
    setLoading(true);
    try {
      const res = await api.post(`/users/${name}/sync`);
      setTransactions(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return { transactions, username, loading, handleUserSubmit };
}

export default usernameLookup;