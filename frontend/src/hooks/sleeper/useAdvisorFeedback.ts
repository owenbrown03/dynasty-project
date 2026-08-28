import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type {
  AdvisorFeedbackEntryItem,
  AdvisorFeedbackRequest,
} from '@/types';

export function useAdvisorFeedback() {
  const mutation = useMutation<void, Error, AdvisorFeedbackRequest>({
    mutationFn: async (payload) => {
      await api.advisor.recordFeedback(payload);
    },
    onSuccess: () => {
      notify.success('Feedback saved — future recommendations will respect it.');
    },
    onError: () => {
      notify.error('Could not save feedback. Try again.');
    },
  });

  return {
    save: (payload: AdvisorFeedbackRequest) => mutation.mutateAsync(payload),
    saving: mutation.isPending,
  };
}


export function useAdvisorLeagueFeedback(
  leagueId: string | undefined,
) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['advisor-feedback', leagueId ?? null],
    queryFn: async () => {
      if (!leagueId) return null;
      const response = await api.advisor.listFeedback(leagueId);
      return response.data;
    },
    enabled: !!leagueId,
    staleTime: 60 * 1000,
  });

  const invalidateLists = async () => {
    await queryClient.invalidateQueries({
      queryKey: ['advisor-feedback'],
    });
  };

  const remove = useMutation({
    mutationFn: async (feedbackId: number) => {
      await api.advisor.deleteFeedback(feedbackId);
    },
    onSuccess: invalidateLists,
  });

  return {
    entries: (query.data?.entries ?? []) as AdvisorFeedbackEntryItem[],
    loading: query.isLoading,
    remove: remove.mutateAsync,
    removing: remove.isPending,
  };
}
