import { type AxiosInstance } from 'axios';

import type { AdvisorSynthesisResponse } from '@/types';

export const advisorEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  getRecommendations: (
    username: string,
    signal?: AbortSignal,
  ) =>
    client.post<AdvisorSynthesisResponse>(
      `${prefix}/${username}/recommendations`,
      null,
      { signal, timeout: 120000 },
    ),
});
