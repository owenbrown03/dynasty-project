import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useBootstrap } from '../useBootstrap';

export function useSleeperConnection() {
  const queryClient = useQueryClient();
  const bootstrapQuery = useBootstrap();

  const [cachedUsername, setCachedUsername] = useState<string | null>(
    () => localStorage.getItem('sleeper_username')
  );

  const sleeper = bootstrapQuery.data?.sleeper;

  useEffect(() => {
    if (sleeper?.sleeper_username) {
      localStorage.setItem('sleeper_username', sleeper.sleeper_username);
      setCachedUsername(sleeper.sleeper_username);
    } else if (sleeper === null && !bootstrapQuery.isLoading) {
      localStorage.removeItem('sleeper_username');
      setCachedUsername(null);
    }
  }, [sleeper, bootstrapQuery.isLoading]);

  const upsertMutation = useMutation({
    mutationFn: api.connection.upsert,

    onSuccess: async (data) => {
      if (data?.sleeper_username) {
        localStorage.setItem('sleeper_username', data.sleeper_username);
        setCachedUsername(data.sleeper_username);
      }
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

  return {
    connection: sleeper ?? null,
    username: sleeper?.sleeper_username ?? cachedUsername,
    avatar: sleeper?.sleeper_avatar ?? null,
    canRead: sleeper?.can_read ?? !!cachedUsername,
    canWrite: sleeper?.can_write ?? false,
    linked: sleeper?.linked ?? !!cachedUsername,
    
    isLoading: bootstrapQuery.isLoading,
    isUpserting: upsertMutation.isPending,
    isReconciling: reconcileMutation.isPending,

    upsertConnection: upsertMutation.mutateAsync,
    reconcileConnection: reconcileMutation.mutateAsync,
  };
}
