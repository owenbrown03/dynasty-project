import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type {
  CommissionerLeagueDuesUpdate,
  CommissionerLeagueNoteUpdate,
  CommissionerOrphansResponse,
  CommissionerWorkspaceResponse,
  Orphan,
  Roster,
  ValueBasis,
} from '@/types';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export function useRosters() {
  const { username } = useSleeperConnection();
  const query = useQuery<Roster[]>({
    queryKey: queryKeys.users.rosters(
      username,
    ),
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
    queryKey: queryKeys.users.orphans(
      username,
    ),
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
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.rosters(
          username,
        ),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.orphans(
          username,
        ),
      });
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
    queryKey: queryKeys.users.commissionerOrphans(
      username,
      valueBasis,
    ),
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


export function useCommissionerWorkspace(
  enabled: boolean,
) {
  const query = useQuery<CommissionerWorkspaceResponse>({
    queryKey: queryKeys.users.commissionerWorkspace,
    queryFn: async () => api.users
      .getCommissionerWorkspace()
      .then((res) => res.data),
    enabled,
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}


export function useSaveCommissionerNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      body: CommissionerLeagueNoteUpdate,
    ) => api.users.saveCommissionerNote(body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.users.commissionerWorkspace,
      });
    },
  });
}


export function useSaveCommissionerDues() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      body: CommissionerLeagueDuesUpdate,
    ) => api.users.saveCommissionerDues(body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.users.commissionerWorkspace,
      });
    },
  });
}
