import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

import type {
  BulkTradeAvailabilityResponse,
  BulkTradePlayerSearchResult,
  BulkTradeProposalRequest,
  BulkTradeProposalResponse,
  TradeDirection,
} from '@/types';


export function useBulkTradePlayerSearch(
  query: string,
) {
  const trimmedQuery = query.trim();

  const search = useQuery<
    BulkTradePlayerSearchResult[]
  >({
    queryKey: queryKeys.trades.bulkPlayerSearch(
      trimmedQuery,
    ),
    queryFn: async () => {
      return api.trades.searchBulkPlayers(
        trimmedQuery,
      ).then(
        response => response.data,
      );
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


export function useBulkTradeAvailability(
  playerId: string | undefined,
  direction: TradeDirection,
  pickSeason: string,
  pickRound: number,
) {
  const {
    canRead,
    username,
  } = useSleeperConnection();

  const query = useQuery<
    BulkTradeAvailabilityResponse
  >({
    queryKey: queryKeys.trades.bulkAvailability(
      username,
      playerId,
      direction,
      pickSeason,
      pickRound,
    ),
    queryFn: async () => {
      if (!playerId) {
        throw new Error(
          'Missing selected player.',
        );
      }

      return api.trades.getBulkAvailability(
        playerId,
        direction,
        pickSeason,
        pickRound,
      ).then(
        response => response.data,
      );
    },
    enabled: (
      canRead
      && !!playerId
      && pickSeason.length === 4
      && pickRound >= 1
    ),
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}


export function useSubmitBulkTradeOffers() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    BulkTradeProposalResponse,
    Error,
    BulkTradeProposalRequest
  >({
    mutationFn: async payload => {
      return api.trades.submitBulkOffers(
        payload,
      ).then(
        response => response.data,
      );
    },

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: queryKeys.trades.bulkAvailabilityRoot,
        }),

        queryClient.invalidateQueries({
          queryKey: queryKeys.leagues.overviewRoot,
        }),

        queryClient.invalidateQueries({
          queryKey: queryKeys.waivers.overviewRoot,
        }),
      ]);
    },
  });

  return {
    submitOffers: mutation.mutate,
    submitting: mutation.isPending,
    success: mutation.isSuccess,
    results: mutation.data?.results ?? [],
    error: mutation.error,
    reset: mutation.reset,
  };
}
