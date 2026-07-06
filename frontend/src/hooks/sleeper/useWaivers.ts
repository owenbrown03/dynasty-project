import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

import type {
  BulkWaiverAvailabilityResponse,
  BulkWaiverClaimRequest,
  BulkWaiverClaimResponse,
  BulkWaiverPlayerSearchResult,
  ValueBasis,
  WaiverAvailablePlayersResponse,
  WaiverClaimRequest,
  WaiverClaimResponse,
  WaiverOverviewResponse,
  WaiverRosterPlayersResponse,
} from '@/types';


export function useWaiverOverview(
  valueBasis: ValueBasis,
) {
  const {
    username,
    canRead,
  } = useSleeperConnection();

  const query = useQuery<WaiverOverviewResponse>({
    queryKey: [
      'waiver-overview',
      username,
      valueBasis,
    ],

    queryFn: async () => {
      return api.waivers
        .getOverview(valueBasis)
        .then((res) => res.data);
    },

    enabled: canRead,
  });

  return {
    data: query.data,
    username,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}


export function useSubmitWaiverClaim() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    WaiverClaimResponse,
    Error,
    WaiverClaimRequest
  >({
    mutationFn: async (
      payload,
    ) => {
      return api.waivers
        .submitClaim(payload)
        .then((res) => res.data);
    },

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            'waiver-overview',
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            'waiver-available-players',
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            'waiver-roster-players',
          ],
        }),
      ]);
    },
  });

  return {
    submitClaim: mutation.mutate,
    submitClaimAsync: mutation.mutateAsync,

    submitting: mutation.isPending,

    success: mutation.isSuccess,
    error: mutation.error,

    reset: mutation.reset,
  };
}


export function useWaiverLeagueOptions() {
  const {
    canRead,
    username,
  } = useSleeperConnection();

  const query = useQuery({
    queryKey: [
      'waiver-leagues',
      username,
    ],

    queryFn: async () => {
      return api.waivers
        .getLeagues()
        .then((res) => res.data);
    },

    enabled: canRead,
  });

  return {
    data: query.data ?? [],
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}


export function useAvailableWaiverPlayers(
  leagueId: string | undefined,
  valueBasis: ValueBasis,
) {
  const {
    canRead,
    username,
  } = useSleeperConnection();

  const query = useQuery<WaiverAvailablePlayersResponse>({
    queryKey: [
      'waiver-available-players',
      username,
      leagueId,
      valueBasis,
    ],

    queryFn: async () => {
      if (!leagueId) {
        throw new Error(
          'Missing waiver league id',
        );
      }

      return api.waivers
        .getAvailablePlayers(
          leagueId,
          valueBasis,
        )
        .then((res) => res.data);
    },

    enabled: (
      canRead
      && !!leagueId
    ),
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}


export function useRosterWaiverPlayers(
  leagueId: string | undefined,
  valueBasis: ValueBasis,
  enabled: boolean,
) {
  const {
    canRead,
    username,
  } = useSleeperConnection();

  const query = useQuery<WaiverRosterPlayersResponse>({
    queryKey: [
      'waiver-roster-players',
      username,
      leagueId,
      valueBasis,
    ],

    queryFn: async () => {
      if (!leagueId) {
        throw new Error(
          'Missing waiver league id',
        );
      }

      return api.waivers
        .getRosterPlayers(
          leagueId,
          valueBasis,
        )
        .then((res) => res.data);
    },

    enabled: (
      canRead
      && !!leagueId
      && enabled
    ),
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}

export function useBulkWaiverPlayerSearch(
  query: string,
) {
  const trimmedQuery = query.trim();

  const search = useQuery<BulkWaiverPlayerSearchResult[]>({
    queryKey: [
      'bulk-waiver-player-search',
      trimmedQuery,
    ],

    queryFn: async () => {
      return api.waivers
        .searchBulkPlayers(trimmedQuery)
        .then((res) => res.data);
    },

    enabled: trimmedQuery.length >= 2,
  });

  return {
    data: search.data ?? [],
    loading: search.isLoading,
    fetching: search.isFetching,
    error: search.error,
  };
}


export function useBulkWaiverAvailability(
  playerId: string | undefined,
  valueBasis: ValueBasis,
) {
  const {
    canRead,
    username,
  } = useSleeperConnection();

  const query = useQuery<BulkWaiverAvailabilityResponse>({
    queryKey: [
      'bulk-waiver-availability',
      username,
      playerId,
      valueBasis,
    ],

    queryFn: async () => {
      if (!playerId) {
        throw new Error(
          'Missing bulk waiver player id',
        );
      }

      return api.waivers
        .getBulkAvailability(
          playerId,
          valueBasis,
        )
        .then((res) => res.data);
    },

    enabled: (
      canRead
      && !!playerId
    ),
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}


export function useSubmitBulkWaiverClaims() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    BulkWaiverClaimResponse,
    Error,
    BulkWaiverClaimRequest
  >({
    mutationFn: async (
      payload,
    ) => {
      return api.waivers
        .submitBulkClaims(payload)
        .then((res) => res.data);
    },

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            'waiver-overview',
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            'waiver-available-players',
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            'waiver-roster-players',
          ],
        }),
        queryClient.invalidateQueries({
          queryKey: [
            'bulk-waiver-availability',
          ],
        }),
      ]);
    },
  });

  return {
    submitBulkClaims: mutation.mutate,
    submitBulkClaimsAsync: mutation.mutateAsync,

    submitting: mutation.isPending,

    data: mutation.data,
    error: mutation.error,

    reset: mutation.reset,
  };
}