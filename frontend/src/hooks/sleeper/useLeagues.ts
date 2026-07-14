import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type {
  LeagueOverview,
  LeagueDetails,
  Dashboard,
  LeagueVisibilityItem,
  LeagueVisibilityUpdate,
  UserLeagueNoteUpdate,
  UserLeagueNoteResponse,
} from '@/types';

import { useSleeperConnection } from '@/hooks/sleeper/useConnection';


export function useLeagueOverview(
  includeHidden = false,
) {
  const { username } = useSleeperConnection();

  const query = useQuery<LeagueOverview[]>({
    queryKey: queryKeys.leagues.overview(
      username,
      includeHidden,
    ),

    queryFn: async () => {
      if (!username) {
        throw new Error('Missing username');
      }

      return api.leagues
        .getOverview(
          username,
          includeHidden,
        )
        .then(res => res.data);
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


export function useLeagueVisibility() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    LeagueVisibilityItem,
    Error,
    {
      leagueId: string;
      payload: LeagueVisibilityUpdate;
    }
  >({
    mutationFn: async ({
      leagueId,
      payload,
    }) => {
      return api.leagues
        .setVisibility(
          leagueId,
          payload,
        )
        .then((res) => res.data);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: queryKeys.leagues.overviewRoot,
        }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.waivers.overviewRoot,
        }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.waivers.leaguesRoot,
        }),
      ]);
    },
  });

  return {
    setLeagueVisibility: mutation.mutateAsync,
    saving: mutation.isPending,
  };
}


export function useLeagueDetails(league_id?: string) {
  const query = useQuery<LeagueDetails>({
    queryKey: queryKeys.leagues.details(
      league_id,
    ),

    queryFn: async () => {
      if (!league_id) {
        throw new Error('Missing league id');
      }

      return api.leagues
        .getDetails(league_id)
        .then(res => res.data);
    },

    enabled: !!league_id,
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
  };
}


export function useLeagueDashboard() {
  const { username } = useSleeperConnection();

  const query = useQuery<Dashboard>({
    queryKey: queryKeys.leagues.dashboard(
      username,
    ),
    queryFn: async () => {
      if (!username) {
        throw new Error('Missing username');
      }

      return api.leagues
        .getDashboard(username)
        .then(res => res.data);
    },
    enabled: !!username,
  });

  return {
    data: query.data,
    username,
    loading: query.isLoading,
    fetching: query.isFetching,
  };
}


export function useSaveUserNote() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    UserLeagueNoteResponse,
    Error,
    UserLeagueNoteUpdate
  >({
    mutationFn: async (payload) => {
      return api.leagues
        .saveNote(payload)
        .then((res) => res.data);
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.leagues.details(data.league_id),
      });
    },
  });

  return {
    saveNote: mutation.mutateAsync,
    saving: mutation.isPending,
  };
}

