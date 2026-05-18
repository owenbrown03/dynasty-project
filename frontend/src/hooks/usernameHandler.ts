import { useEffect, useState } from 'react';

import api from '../api/client.ts';
import type { Roster, Transaction } from '../types/index.ts';

// TODO: need to implement these apis
// /api/v1/users/{username}/sync
// /api/v1/trades/{username}/sync-leaguemates
// /api/v1/players/sync

export function useRosterLoader(username: string | undefined) {
  const [loading, setLoading] = useState(false);
  const [rosters, setRosters] = useState<Roster[]>([]);

  useEffect(() => {
    if (!username) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/api/v1/users/${username}/rosters`);
        setRosters(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [username]);

  return { rosters, loading };
}

export function useTradeLoader(username: string | undefined) {
  const [loading, setLoading] = useState(false);
  const [trades, setTrades] = useState<Transaction[]>([]);

  useEffect(() => {
    if (!username) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/api/v1/trades/${username}/trade-signals`);
        setTrades(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [username]);

  return { trades, loading };
}