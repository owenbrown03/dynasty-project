import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type { TradeBlockToggleRequest, Transaction } from '@/types';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export function useTrades(cheap = false) {
  const { username } = useSleeperConnection();
  const query = useQuery<Transaction[]>({
    queryKey: queryKeys.trades.signals(
      username,
      cheap,
    ),
    queryFn: async ({ signal }) => {
      if (!username) throw notify.error('Missing username!');
      return api.trades.getTradeSignals(username, cheap, signal).then(res => res.data);
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

export function useToggleTradeBlock() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: TradeBlockToggleRequest) => {
      const response = await api.trades.toggleTradeBlock(payload);
      return response.data;
    },
    onSuccess: (data) => {
      notify.success(data.message || (data.on_block ? 'Added to trade block' : 'Removed from trade block'));
      void queryClient.invalidateQueries({
        queryKey: queryKeys.leagues.detailsRoot,
      });
    },
    onError: (error: unknown) => {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      const message = err?.response?.data?.detail || err?.message || 'Failed to update trade block';
      notify.error(message);
    },
  });
}

