import { useMutation } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type { AdvisorFeedbackRequest } from '@/types';

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
