import { type AxiosInstance } from 'axios';

import type {
  AdvisorDigestResponse,
  AdvisorFeedbackRequest,
  AdvisorSynthesisResponse,
} from '@/types';

export const advisorEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  getRecommendations: (
    username: string,
    options?: {
      leagueId?: string;
      signal?: AbortSignal;
    },
  ) =>
    client.post<AdvisorSynthesisResponse>(
      `${prefix}/${username}/recommendations`,
      null,
      {
        params: options?.leagueId
          ? { league_id: options.leagueId }
          : undefined,
        signal: options?.signal,
        timeout: 120000,
      },
    ),

  recordFeedback: (
    payload: AdvisorFeedbackRequest,
  ) => client.post(`${prefix}/feedback`, payload),

  getDigest: (
    username: string,
    signal?: AbortSignal,
  ) =>
    client.get<AdvisorDigestResponse>(
      `${prefix}/${username}/digest`,
      { signal },
    ),
});
