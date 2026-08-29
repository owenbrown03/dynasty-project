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
  PersonalValueRankingsResetRequest,
  PersonalValueRankingsResetResponse,
  PersonalValueRankingsUpdateRequest,
  PersonalValueUnderdogSyncRequest,
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
    queryFn: async ({ signal }) => {
      if (!leagueId) {
        throw new Error('Missing league id');
      }

      return api.personal_values
        .getPool(leagueId, signal)
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
    queryFn: async ({ signal }) => {
      return api.personal_values
        .search(
          normalizedQuery,
          leagueId,
          signal,
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
    queryFn: async ({ signal }) => {
      if (!leagueId || !playerId) {
        throw new Error('Missing personal values context');
      }

      return api.personal_values
        .getPlayer(
          leagueId,
          playerId,
          signal,
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


async function invalidatePersonalValuesDependentQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  leagueId?: string,
) {
  await Promise.all([
    queryClient.invalidateQueries({
      queryKey: queryKeys.leagues.detailsRoot,
    }),
    queryClient.invalidateQueries({
      queryKey: queryKeys.leagues.overviewRoot,
    }),
    queryClient.invalidateQueries({
      queryKey: queryKeys.leagues.dashboardRoot,
    }),
    queryClient.invalidateQueries({
      queryKey: queryKeys.players.personalDetailRoot,
    }),
    queryClient.invalidateQueries({
      queryKey: ['personal-values-rankings'],
    }),
    queryClient.invalidateQueries({
      queryKey: ['rosters'],
    }),
    queryClient.invalidateQueries({
      queryKey: queryKeys.waivers.rosterPlayersRoot,
    }),
    queryClient.invalidateQueries({
      queryKey: queryKeys.waivers.overviewRoot,
    }),
    leagueId
      ? queryClient.invalidateQueries({
          queryKey: [
            ...queryKeys.players.personalDetailRoot,
            'pool',
            leagueId,
          ],
        })
      : Promise.resolve(),
  ]);
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

      await invalidatePersonalValuesDependentQueries(
        queryClient,
        variables.leagueId,
      );
    },
  });

  return {
    savePersonalValue: mutation.mutateAsync,
    saving: mutation.isPending,
    error: mutation.error,
  };
}


export function usePersonalValueRankings(
  leagueId: string | undefined,
  position: string,
  scope: string,
) {
  const query = useQuery({
    queryKey: queryKeys.players.personalRankings(
      leagueId,
      position,
      scope,
    ),
    queryFn: async () => {
      if (!leagueId) return null;
      const response = await api.personal_values.getRankings(
        leagueId,
        position,
        scope,
      );
      return response.data;
    },
    enabled: !!leagueId,
    staleTime: 30 * 1000,
  });

  return {
    rankings: query.data?.entries ?? [],
    season: query.data?.season ?? null,
    loading: query.isLoading,
    fetching: query.isFetching,
    refetch: query.refetch,
  };
}

export function useSavePersonalValueRankings() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (
      payload: PersonalValueRankingsUpdateRequest,
    ) => {
      const response = await api.personal_values.saveRankings(
        payload,
      );
      return response.data;
    },
    onSuccess: async (_data, variables) => {
      await invalidatePersonalValuesDependentQueries(
        queryClient,
        variables.league_id,
      );
    },
  });

  return {
    saveRankings: mutation.mutateAsync,
    saving: mutation.isPending,
    error: mutation.error,
  };
}


export function useResetPersonalValueRankings() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (
      payload: PersonalValueRankingsResetRequest,
    ) => {
      const response = await api.personal_values.resetRankings(
        payload,
      );
      return response.data as PersonalValueRankingsResetResponse;
    },
    onSuccess: async (_data, variables) => {
      await invalidatePersonalValuesDependentQueries(
        queryClient,
        variables.league_id,
      );
    },
  });

  return {
    resetRankings: mutation.mutateAsync,
    saving: mutation.isPending,
  };
}


export function useSyncUnderdogDefaults() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (
      payload: PersonalValueUnderdogSyncRequest,
    ) => {
      const response = await api.personal_values.syncUnderdog(
        payload,
      );
      return response.data;
    },
    onSuccess: async (_data, variables) => {
      await invalidatePersonalValuesDependentQueries(
        queryClient,
        variables.league_id,
      );
    },
  });

  return {
    syncDefaults: mutation.mutateAsync,
    saving: mutation.isPending,
  };
}
