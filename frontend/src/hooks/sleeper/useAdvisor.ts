import { useMutation } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { appQueryClient } from '@/api/query-client';
import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type {
  AdvisorSynthesisResponse,
} from '@/types';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

function extractErrorDetail(
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
        { leagueId },
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
    recommendations: mutation.data ?? null,
    loading: mutation.isPending,
    error: mutation.error,
    errorMessage: mutation.error
      ? extractErrorDetail(mutation.error)
        ?? 'AI advisor could not generate recommendations. Try again shortly.'
      : null,
    generate: () => mutation.mutate(),
    reset: () => mutation.reset(),
  };
}
