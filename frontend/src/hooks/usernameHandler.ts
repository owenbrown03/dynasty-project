import { useEffect, useState, useRef } from 'react';
import api from '../api/client.ts';
import { useApi } from '../context/ApiContext.tsx';
import type { Roster, Transaction, Orphan } from '../types/index.ts';

export function useUserSync(username: string | undefined) {
  const { isCalling, executeCall } = useApi();
  const syncKey = `user-sync-${username}`;
  const hasFetchedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!username || hasFetchedRef.current === username) return;
    hasFetchedRef.current = username;

    const debounceTimer = setTimeout(() => {
      executeCall(syncKey, async () => {
        return await api.post(`/api/v1/users/${username}/sync`);
      }).catch((err) => console.error("User sync pipeline failed:", err));
    }, 200);

    return () => {
      clearTimeout(debounceTimer);
    };
  }, [username]);

  return { loading: isCalling(syncKey) };
}

export function useLeaguemateSync(username: string | undefined) {
  const { isCalling, executeCall } = useApi();
  const syncKey = `leaguemates-sync-${username}`;
  const hasFetchedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!username || hasFetchedRef.current === username) return;
    hasFetchedRef.current = username;

    const debounceTimer = setTimeout(() => {
      executeCall(syncKey, async () => {
        return await api.post(`/api/v1/trades/${username}/sync-leaguemates`);
      }).catch((err) => console.error("Leaguemate sync pipeline failed:", err));
    }, 200);

    return () => {
      clearTimeout(debounceTimer);
    };
  }, [username]);

  return { loading: isCalling(syncKey) };
}

export function useRosterLoader(username: string | undefined) {
  const { isCalling, executeCall } = useApi();
  const apiKey = `rosters-load-${username}`;
  const [rosters, setRosters] = useState<Roster[]>([]);
  const hasFetchedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!username || hasFetchedRef.current === username) return;
    hasFetchedRef.current = username;

    executeCall(apiKey, async () => {
      const res = await api.get(`/api/v1/users/${username}/rosters`);
      setRosters(res.data);
      return res;
    }).catch((err) => console.error(err));
  }, [username]);

  return { rosters, loading: isCalling(apiKey) };
}

export function useTradeLoader(username: string | undefined) {
  const { isCalling, executeCall } = useApi();
  const apiKey = `trades-load-${username}`;
  const [trades, setTrades] = useState<Transaction[]>([]);
  const hasFetchedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!username || hasFetchedRef.current === username) return;
    hasFetchedRef.current = username;

    executeCall(apiKey, async () => {
      const res = await api.get(`/api/v1/trades/${username}/trade-signals`);
      setTrades(res.data);
      return res;
    }).catch((err) => console.error(err));
  }, [username]);

  return { trades, loading: isCalling(apiKey) };
}

export function useOrphanLoader(username: string | undefined) {
  const { isCalling, executeCall } = useApi();
  const apiKey = `orphans-load-${username}`;
  const [orphans, setOrphans] = useState<Orphan[]>([]);
  const hasFetchedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!username || hasFetchedRef.current === username) return;
    hasFetchedRef.current = username;

    executeCall(apiKey, async () => {
      const res = await api.get(`/api/v1/users/${username}/orphans`);
      setOrphans(res.data);
      return res;
    }).catch((err) => console.error(err));
  }, [username]);

  return { orphans, loading: isCalling(apiKey) };
}