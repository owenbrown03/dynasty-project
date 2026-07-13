import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type {
  PersonalValueDetail,
  PersonalValuePoolResponse,
  PersonalValueSearchResult,
  PersonalValueUpdateRequest,
} from '@/types';


export function usePersonalValuePool(
  leagueId?: string,
) {
  const query = useQuery<PersonalValuePoolResponse>({
    queryKey: [
      ...queryKeys.players.personalDetailRoot,
      'pool',
      leagueId ?? null,
    ],
    queryFn: async () => {
      if (!leagueId) {
        throw new Error('Missing league id');
      }

      return api.personal_values
        .getPool(leagueId)
        .then((res) => res.data);
    },
    enabled: Boolean(leagueId),
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}


export function usePersonalValueSearch(
  query: string,
  leagueId?: string,
) {
  const normalizedQuery = query.trim();
  const enabled = normalizedQuery.length >= 2;
  const result = useQuery<PersonalValueSearchResult[]>({
    queryKey: queryKeys.players.personalSearch(
      `${leagueId ?? 'global'}:${normalizedQuery}`,
    ),
    queryFn: async () => {
      return api.personal_values
        .search(
          normalizedQuery,
          leagueId,
        )
        .then((res) => res.data);
    },
    enabled,
  });

  return {
    data: result.data ?? [],
    loading: result.isLoading,
    fetching: result.isFetching,
    enabled,
  };
}


export function usePersonalValueDetail(
  leagueId?: string,
  playerId?: string,
) {
  const query = useQuery<PersonalValueDetail>({
    queryKey: queryKeys.players.personalDetail(
      leagueId,
      playerId,
    ),
    queryFn: async () => {
      if (!leagueId || !playerId) {
        throw new Error('Missing personal values context');
      }

      return api.personal_values
        .getPlayer(
          leagueId,
          playerId,
        )
        .then((res) => res.data);
    },
    enabled: Boolean(leagueId && playerId),
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}


export function useSavePersonalValueDetail() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    PersonalValueDetail,
    Error,
    {
      leagueId: string;
      playerId: string;
      payload: PersonalValueUpdateRequest;
    }
  >({
    mutationFn: async ({
      leagueId,
      playerId,
      payload,
    }) => {
      return api.personal_values
        .savePlayer(
          leagueId,
          playerId,
          payload,
        )
        .then((res) => res.data);
    },
    onSuccess: async (
      data,
      variables,
    ) => {
      queryClient.setQueryData(
        queryKeys.players.personalDetail(
          variables.leagueId,
          variables.playerId,
        ),
        data,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: queryKeys.players.personalDetailRoot,
        }),
        queryClient.invalidateQueries({
          queryKey: [
            ...queryKeys.players.personalDetailRoot,
            'pool',
            variables.leagueId,
          ],
        }),
      ]);
    },
  });

  return {
    savePersonalValue: mutation.mutateAsync,
    saving: mutation.isPending,
    error: mutation.error,
  };
}
