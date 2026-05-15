import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import api from '../api/client.ts';
import { useUsername } from '../context/usernameContext';
import type { Roster, Transaction } from '../types/index.ts';

export function useUsernameLookup() {
  const [loading, setLoading] = useState(false);
  const { username, setUsername } = useUsername();

  const handleUserSubmit = async (inputName: string) => {
    if (!inputName || inputName === username) return;
    setUsername(inputName);
    setLoading(true);
    try {
      await api.post(`/users/${inputName}/sync`);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return { username, loading, handleUserSubmit };
}

export function useRouteUsername() {
  const { routeUsername } = useParams();
  const { username, setUsername } = useUsername();

  useEffect(() => {
    if (routeUsername && routeUsername !== username) {
      setUsername(routeUsername);
    }
  }, [routeUsername, setUsername, username]);

  return routeUsername ?? username;
}

export function useRosterLoader(username: string) {
  const [loading, setLoading] = useState(false);
  const [rosters, setRosters] = useState<Roster[]>([]);

  useEffect(() => {
    if (!username) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/users/${username}/rosters`);
        setRosters(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [username]); // Refetch whenever username changes

  return { rosters, loading };
}

export function useTradeLoader(username: string) {
  const [loading, setLoading] = useState(false);
  const [trades, setTrades] = useState<Transaction[]>([]);

  useEffect(() => {
    if (!username) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/users/${username}/trades`);
        setTrades(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [username]); // Refetch whenever username changes

  return { trades, loading };
}
