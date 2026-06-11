import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import type { SleeperConnection } from '@/types';

const KEY = ['sleeper-connection'] as const;

export function useSleeperConnection() {
  const queryClient = useQueryClient();

  const query = useQuery<SleeperConnection>({
    queryKey: KEY,
    queryFn: api.connection.get,
    retry: (failureCount, error: any) => {
      if (error?.response?.status === 400) return false;
      return failureCount < 3;
    },
  });

  const upsertMutation = useMutation({
    mutationFn: api.connection.upsert,
    onSuccess: (connection) => {
      queryClient.setQueryData(KEY, connection);
      queryClient.invalidateQueries({ queryKey: KEY });
    },
  });

  const reconcileMutation = useMutation({
      mutationFn: api.connection.reconcile,
      onSuccess: (connection) => {
        queryClient.setQueryData(KEY, connection);
        queryClient.invalidateQueries({ queryKey: KEY });
      },
    });

  return {
    connection: query.data ?? null,

    username: query.data?.username ?? null,
    canRead: query.data?.can_read ?? false,
    canWrite: query.data?.can_write ?? false,

    isLoading: query.isLoading,
    isFetching: query.isFetching,

    isUpserting: upsertMutation.isPending,
    isReconciling: reconcileMutation.isPending,

    upsertConnection: upsertMutation.mutateAsync,
    reconcileConnection: reconcileMutation.mutateAsync,
  };
}