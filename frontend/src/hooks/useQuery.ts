// src/hooks/useQuery.ts
import { useState, useEffect } from 'react';
import { useApi } from '@/context/ApiContext';

export function useQuery<T>(
  key: string,
  fetchFn: () => Promise<{ data: T }>,
  deps: any[] = []
) {
  const { executeCall, isCalling } = useApi();
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    executeCall(key, async () => {
      const res = await fetchFn();
      setData(res.data);
      return res;
    }).catch(console.error);
  }, deps);

  return { data, loading: isCalling(key) };
}