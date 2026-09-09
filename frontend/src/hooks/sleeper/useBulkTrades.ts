import { useMemo } from 'react';
import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

import type {
  BulkTradeAvailabilityRequest,
  BulkTradeAvailabilityResponse,
  BulkTradePickRequest,
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
    queryFn: async ({ signal }) => {
      return api.trades.searchBulkPlayers(
        trimmedQuery,
        signal,
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
    queryFn: async ({ signal }) => {
      if (!payload) {
        throw new Error(
          'Missing selected trade package.',
        );
      }

      return api.trades.getBulkAvailability(
        payload,
        signal,
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
  signal?: AbortSignal,
) {
  return api.trades.getTradeCalculatorPickValue(
    season,
    round,
    slot,
    totalRosters,
    numQbs,
    ppr,
    signal,
  ).then(
    (
      response,
    ): TradeCalculatorPickValueResponse => response.data,
  );
}


export function useBulkTradePickValues(
  picks: BulkTradePickRequest[],
  totalRosters = 12,
  numQbs = 2,
  ppr = 1,
): Map<string, TradeCalculatorPickValueResponse> {
  const uniquePicks = useMemo(() => {
    const map = new Map<string, BulkTradePickRequest>();
    for (const p of picks) {
      if (p.season && p.round) {
        map.set(`${p.season}-${p.round}`, p);
      }
    }
    return Array.from(map.values());
  }, [picks]);

  const results = useQueries({
    queries: uniquePicks.map((pick) => ({
      queryKey: ['tradeCalculatorPickValue', pick.season, pick.round, totalRosters, numQbs, ppr],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        fetchTradeCalculatorPickValue(
          pick.season,
          pick.round,
          null,
          totalRosters,
          numQbs,
          ppr,
          signal,
        ),
      staleTime: 1000 * 60 * 30,
    })),
  });

  return useMemo(() => {
    const pickMap = new Map<string, TradeCalculatorPickValueResponse>();
    results.forEach((res, idx) => {
      const pick = uniquePicks[idx];
      if (pick && res.data) {
        pickMap.set(`${pick.season}-${pick.round}`, res.data as TradeCalculatorPickValueResponse);
      }
    });
    return pickMap;
  }, [results, uniquePicks]);
}

