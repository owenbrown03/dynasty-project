import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useBootstrap } from '../useBootstrap';

export function useSleeperConnection() {
  const queryClient = useQueryClient();
  const bootstrapQuery = useBootstrap();

  const upsertMutation = useMutation({
    mutationFn: api.connection.upsert,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });
    },
  });

  const reconcileMutation = useMutation({
    mutationFn: api.connection.reconcile,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });
    },
  });

  const sleeper = bootstrapQuery.data?.sleeper;

  return {
    connection: sleeper ?? null,
    username: sleeper?.sleeper_username ?? null,
    avatar: sleeper?.sleeper_avatar ?? null,
    canRead: sleeper?.can_read ?? false,
    canWrite: sleeper?.can_write ?? false,
    linked: sleeper?.linked ?? false,
    
    isLoading:bootstrapQuery.isLoading,
    isUpserting: upsertMutation.isPending,
    isReconciling: reconcileMutation.isPending,

    upsertConnection: upsertMutation.mutateAsync,
    reconcileConnection: reconcileMutation.mutateAsync,
  };
}
