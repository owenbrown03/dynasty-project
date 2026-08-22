import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type { Transaction } from '@/types';
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
