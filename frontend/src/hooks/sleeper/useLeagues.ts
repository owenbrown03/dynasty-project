import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type {
  Bootstrap,
  LeagueOverview,
  LeagueSelectorItem,
  LeagueDetails,
  Dashboard,
  LeagueFocusItem,
  LeagueFocusUpdate,
  LeagueVisibilityItem,
  LeagueVisibilityUpdate,
  UserLeagueNoteUpdate,
  UserLeagueNoteResponse,
} from '@/types';

import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useBootstrap } from '@/hooks/useBootstrap';


function buildLeagueDetailsViewerKey(
  bootstrap: Bootstrap | undefined,
) {
  if (!bootstrap) {
    return 'anonymous';
  }

  return JSON.stringify({
    authenticated: bootstrap.authenticated,
    siteUserId: bootstrap.site_user?.id ?? null,
    valuePreference: bootstrap.value_preference ?? null,
    warValueSettings:
      bootstrap.war_value_settings,
    draftPickProjectionSettings:
      bootstrap.draft_pick_projection_settings,
  });
}


export function useLeagueOverview(
  includeHidden = false,
) {
  const { username } = useSleeperConnection();

  const query = useQuery<LeagueOverview[]>({
    queryKey: queryKeys.leagues.overview(
      username,
      includeHidden,
    ),

    queryFn: async ({ signal }) => {
      if (!username) {
        throw new Error('Missing username');
      }

      return api.leagues
        .getOverview(
          username,
          includeHidden,
          signal,
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


export function useLeagueSelector(
  includeHidden = false,
) {
  const { username } = useSleeperConnection();

  const query = useQuery<LeagueSelectorItem[]>({
    queryKey: queryKeys.leagues.selector(
      username,
      includeHidden,
    ),

    queryFn: async ({ signal }) => {
      if (!username) {
        throw new Error('Missing username');
      }

      return api.leagues
        .getSelector(
          username,
          includeHidden,
          signal,
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
          queryKey: queryKeys.leagues.selectorRoot,
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



export function useLeagueFocus() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    LeagueFocusItem,
    Error,
    {
      leagueId: string;
      payload: LeagueFocusUpdate;
    }
  >({
    mutationFn: async ({
      leagueId,
      payload,
    }) => {
      return api.leagues
        .setFocus(
          leagueId,
          payload,
        )
        .then((res) => res.data);
    },
    onSuccess: (_response, variables) => {
      // 1. Update League Overview queries in-place without refetching
      queryClient.setQueriesData<LeagueOverview[]>(
        { queryKey: queryKeys.leagues.overviewRoot },
        (previous) =>
          previous
            ? previous.map((league) =>
                league.league_id === variables.leagueId
                  ? { ...league, is_focused: variables.payload.focused }
                  : league,
              )
            : previous,
      );

      // 2. Update League Selector queries in-place without refetching
      queryClient.setQueriesData<LeagueSelectorItem[]>(
        { queryKey: queryKeys.leagues.selectorRoot },
        (previous) =>
          previous
            ? previous.map((league) =>
                league.league_id === variables.leagueId
                  ? { ...league, is_focused: variables.payload.focused }
                  : league,
              )
            : previous,
      );

      // 3. Update Dashboard queries in-place (both cheap and full variants) without expensive refetching
      queryClient.setQueriesData<Dashboard>(
        { queryKey: queryKeys.leagues.dashboardRoot },
        (previous) =>
          previous
            ? {
                ...previous,
                leagues: previous.leagues.map((league) =>
                  league.league_id === variables.leagueId
                    ? { ...league, is_focused: variables.payload.focused }
                    : league,
                ),
              }
            : previous,
      );
    },
  });

  return {
    setLeagueFocus: mutation.mutateAsync,
    saving: mutation.isPending,
  };
}

export function useLeagueDetails(league_id?: string, cheap = false) {
  const bootstrap = useBootstrap();
  const viewerKey =
    buildLeagueDetailsViewerKey(
      bootstrap.data
    );

  const query = useQuery<LeagueDetails>({
    queryKey: queryKeys.leagues.details(
      league_id,
      viewerKey,
      cheap,
    ),

    queryFn: async ({ signal }) => {
      if (!league_id) {
        throw new Error('Missing league id');
      }

      return api.leagues
        .getDetails(league_id, cheap, signal)
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


export function useLeagueDashboard(cheap = false) {
  const { username } = useSleeperConnection();

  const query = useQuery<Dashboard>({
    queryKey: queryKeys.leagues.dashboard(
      username,
      cheap,
    ),
    queryFn: async ({ signal }) => {
      if (!username) {
        throw new Error('Missing username');
      }

      return api.leagues
        .getDashboard(username, cheap, signal)
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
  const bootstrap = useBootstrap();

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
    onSuccess: (response, variables) => {
      const viewerKey = buildLeagueDetailsViewerKey(
        bootstrap.data,
      );

      for (const cheap of [true, false]) {
        queryClient.setQueryData<LeagueDetails>(
          queryKeys.leagues.details(
            variables.league_id,
            viewerKey,
            cheap,
          ),
          (previous) =>
            previous
              ? { ...previous, note: response.note }
              : previous,
        );
      }
    },
  });

  return {
    saveNote: mutation.mutateAsync,
    saving: mutation.isPending,
  };
}


export function useSyncLeague() {
  const queryClient = useQueryClient();

  const mutation = useMutation<{ status: string; league_id: string }, Error, string>({
    mutationFn: async (leagueId: string) => {
      return api.leagues.syncLeague(leagueId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        predicate: (query) => {
          const key = query.queryKey;
          if (!Array.isArray(key)) return false;
          // Invalidate details for this league or any league/dashboard queries
          if (key[0] === 'leagues' && (key[1] === 'details' || key[1] === 'overview' || key[1] === 'selector')) {
            return true;
          }
          if (key[0] === 'dashboard' || key[0] === 'users') {
            return true;
          }
          return false;
        },
      });
    },
  });

  return {
    syncLeague: mutation.mutateAsync,
    isSyncing: mutation.isPending,
  };
}
