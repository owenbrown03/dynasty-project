import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import type {
  CommissionerOrphansResponse,
  Orphan,
  Roster,
  ValueBasis,
} from '@/types';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export function useRosters() {
  const { username } = useSleeperConnection();
  const query = useQuery<Roster[]>({
    queryKey: ['rosters', username],
    queryFn: async () => {
      if (!username) throw new Error('Missing username');
      return api.users.getRosters(username).then(res => res.data);
    },
    enabled: !!username,
  });

  return {
    data: query.data ?? [],
    username,
    loading: query.isLoading,
    fetching: query.isFetching,
  };
}

export function useOrphans() {
  const { username } = useSleeperConnection();
  const query = useQuery<Orphan[]>({
    queryKey: ['orphans', username],
    queryFn: async () => {
      if (!username) throw new Error('Missing username');
      return api.users.getOrphans(username).then(res => res.data);
    },
    enabled: !!username,
  });

  return {
    data: query.data ?? [],
    username,
    loading: query.isLoading,
    fetching: query.isFetching,
  };
}

export function useSync() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: api.users.sync,

    onSuccess: (_, username) => {
      queryClient.invalidateQueries({ queryKey: ['rosters', username] });
      queryClient.invalidateQueries({ queryKey: ['orphans', username] });
    },
  });

  return {
    sync: mutation.mutateAsync,
    isSyncing: mutation.isPending,
  };
}


export function useCommissionerOrphans(
  username: string | null | undefined,
  valueBasis: ValueBasis,
) {
  const query = useQuery<CommissionerOrphansResponse>({
    queryKey: [
      'commissioner-orphans',
      username,
      valueBasis,
    ],
    queryFn: async () => {
      if (!username) {
        throw new Error('Missing username');
      }

      return api.users
        .getCommissionerOrphans(
          username,
          valueBasis,
        )
        .then((res) => res.data);
    },
    enabled: !!username,
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}
