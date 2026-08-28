import { type AxiosInstance } from 'axios';

import type {
  AdvisorDigestResponse,
  AdvisorDirectivesResponse,
  AdvisorFeedbackEntryListResponse,
  AdvisorFeedbackRequest,
  AdvisorInvalidateResponse,
  AdvisorSynthesisResponse,
} from '@/types';

export const advisorEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  listFeedback: (
    leagueId: string,
    signal?: AbortSignal,
  ) => client.get<AdvisorFeedbackEntryListResponse>(
    `${prefix}/feedback`,
    {
      params: { league_id: leagueId },
      signal,
    },
  ),
  deleteFeedback: (feedbackId: number) =>
    client.delete<{ id: number; deleted: boolean }>(
      `${prefix}/feedback/${feedbackId}`,
    ),
  invalidate: (
    username: string,
    leagueId?: string,
  ) => client.post<AdvisorInvalidateResponse>(
    `${prefix}/${username}/invalidate`,
    null,
    {
      params: leagueId ? { league_id: leagueId } : {},
    },
  ),
  getDirectives: (
    username: string,
    options?: {
      leagueId?: string;
      signal?: AbortSignal;
    },
  ) =>
    client.get<AdvisorDirectivesResponse>(
      `${prefix}/${username}/directives`,
      {
        params: {
          ...(options?.leagueId
            ? { league_id: options.leagueId }
            : {}),
        },
        signal: options?.signal,
      },
    ),

  getRecommendations: (
    username: string,
    options?: {
      leagueId?: string;
      force?: boolean;
      signal?: AbortSignal;
    },
  ) =>
    client.post<AdvisorSynthesisResponse>(
      `${prefix}/${username}/recommendations`,
      null,
      {
        params: {
          ...(options?.leagueId
            ? { league_id: options.leagueId }
            : {}),
          ...(options?.force ? { force: true } : {}),
        },
        signal: options?.signal,
        timeout: 120000,
      },
    ),

  getCachedRecommendations: async (
    username: string,
    options?: {
      leagueId?: string;
      signal?: AbortSignal;
    },
  ) => {
    const response = await client.get<AdvisorSynthesisResponse>(
      `${prefix}/${username}/recommendations`,
      {
        params: options?.leagueId
          ? { league_id: options.leagueId }
          : undefined,
        signal: options?.signal,
      },
    );

    return response.data ?? null;
  },

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
