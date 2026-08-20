import { type AxiosInstance } from 'axios';

import type { Bootstrap } from '@/types/index';

export const bootstrapEndpoints = (client: AxiosInstance, prefix: string) => ({
  bootstrap: async (
    signal?: AbortSignal,
  ): Promise<Bootstrap> => {
    const res = await client.get<Bootstrap>(prefix, { signal });
    return res.data;
  },
});
