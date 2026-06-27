import { type AxiosInstance } from 'axios';

import type { Bootstrap } from '@/types/index';

export const bootstrapEndpoints = (client: AxiosInstance, prefix: string) => ({
  bootstrap: async (): Promise<Bootstrap> => {
    const res = await client.get<Bootstrap>(prefix);
    return res.data;
  },
});