import { type AxiosInstance } from 'axios';
import { type SleeperConnection } from '@/types';

export const connectionEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({

  get: async (
    signal?: AbortSignal,
  ): Promise<SleeperConnection> => {
    const res = await client.get<SleeperConnection>(prefix, { signal });
    return res.data;
  },

  upsert: async (username: string): Promise<SleeperConnection> => {
    const res = await client.post<SleeperConnection>(
      `${prefix}/upsert`,
      { sleeper_username: username },
    );

    return res.data;
  },

  reconcile: async (
    signal?: AbortSignal,
  ): Promise<SleeperConnection> => {
    const res = await client.post<SleeperConnection>(
      `${prefix}/reconcile`,
      undefined,
      { signal },
    );
    return res.data;
  },
});
