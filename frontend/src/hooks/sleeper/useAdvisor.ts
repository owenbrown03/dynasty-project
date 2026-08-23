import { useMutation, useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { appQueryClient } from '@/api/query-client';
import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type {
  AdvisorSynthesisResponse,
} from '@/types';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export function extractErrorDetail(
  error: Error,
): string | null {
  const response = (
    error as unknown as {
      response?: { data?: { detail?: string } };
    }
  ).response;

  return response?.data?.detail ?? null;
}

export function useAdvisorRecommendations(
  options?: {
    leagueId?: string;
  },
) {
  const { username } = useSleeperConnection();
  const leagueId = options?.leagueId;

  const cachedQuery = useQuery({
    queryKey: queryKeys.advisor.cachedRecommendations(
      username,
      leagueId,
    ),
    queryFn: async () => {
      if (!username) return null;
      return api.advisor.getCachedRecommendations(username, {
        leagueId,
      });
    },
    enabled: !!username,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const mutation = useMutation<
    AdvisorSynthesisResponse,
    Error,
    void
  >({
    mutationKey: queryKeys.advisor.recommendations(
      username,
      leagueId,
    ),
    mutationFn: async () => {
      if (!username) throw notify.error('Missing username!');
      const response = await api.advisor.getRecommendations(
        username,
        { leagueId, force: true },
      );
      return response.data;
    },
    onSuccess: (data) => {
      appQueryClient.setQueryData(
        queryKeys.advisor.recommendations(
          username,
          leagueId,
        ),
        data,
      );
      appQueryClient.setQueryData(
        queryKeys.advisor.cachedRecommendations(
          username,
          leagueId,
        ),
        data,
      );
    },
    onError: (error) => {
      notify.error(
        extractErrorDetail(error)
          ?? 'AI advisor could not generate recommendations. Try again shortly.',
      );
    },
  });

  return {
    username,
    recommendations: mutation.data
      ?? (cachedQuery.data ?? null),
    cachedLoading: cachedQuery.isLoading,
    loading: mutation.isPending,
    error: mutation.error,
    errorMessage: mutation.error
      ? extractErrorDetail(mutation.error)
        ?? 'AI advisor could not generate recommendations. Try again shortly.'
      : null,
    generate: () => mutation.mutate(),
    reset: () => {
      mutation.reset();
      appQueryClient.removeQueries({
        queryKey: queryKeys.advisor.cachedRecommendations(
          username,
          leagueId,
        ),
      });
    },
  };
}
