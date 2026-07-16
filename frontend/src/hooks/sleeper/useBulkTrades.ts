import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

import type {
  BulkTradeAvailabilityRequest,
  BulkTradeAvailabilityResponse,
  BulkTradePlayerSearchResult,
  BulkTradeProposalRequest,
  BulkTradeProposalResponse,
  TradeCalculatorPickValueResponse,
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
  payload: BulkTradeAvailabilityRequest | null,
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
      JSON.stringify(payload),
    ),
    queryFn: async () => {
      if (!payload) {
        throw new Error(
          'Missing selected trade package.',
        );
      }

      return api.trades.getBulkAvailability(
        payload,
      ).then(
        response => response.data,
      );
    },
    enabled: (
      canRead
      && !!payload
      && (
        payload.send_player_ids.length
        + payload.send_picks.length
        > 0
      )
      && (
        payload.receive_player_ids.length
        + payload.receive_picks.length
        > 0
      )
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


export async function fetchTradeCalculatorPickValue(
  season: string,
  round: number,
  slot: number | null,
  totalRosters: number,
  numQbs: number,
  ppr: number,
) {
  return api.trades.getTradeCalculatorPickValue(
    season,
    round,
    slot,
    totalRosters,
    numQbs,
    ppr,
  ).then(
    (
      response,
    ): TradeCalculatorPickValueResponse => response.data,
  );
}
