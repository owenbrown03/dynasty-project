import { useMutation } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { appQueryClient } from '@/api/query-client';
import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type { AdvisorSynthesisResponse } from '@/types';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export function useAdvisorRecommendations() {
  const { username } = useSleeperConnection();

  const mutation = useMutation<
    AdvisorSynthesisResponse,
    Error,
    void
  >({
    mutationKey: queryKeys.advisor.recommendations(username),
    mutationFn: async () => {
      if (!username) throw notify.error('Missing username!');
      const response = await api.advisor.getRecommendations(username);
      return response.data;
    },
    onSuccess: (data) => {
      appQueryClient.setQueryData(
        queryKeys.advisor.recommendations(username),
        data,
      );
    },
  });

  return {
    username,
    recommendations: mutation.data ?? null,
    loading: mutation.isPending,
    error: mutation.error,
    generate: () => mutation.mutate(),
    reset: () => mutation.reset(),
  };
}
