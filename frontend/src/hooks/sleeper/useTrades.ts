import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type { Transaction } from '@/types';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export function useTrades() {
  const { username } = useSleeperConnection();
  const query = useQuery<Transaction[]>({
    queryKey: ['trade-signals', username],
    queryFn: async () => {
      if (!username) throw notify.error('Missing username!');
      return api.trades.getTradeSignals(username).then(res => res.data);
    },
    enabled: !!username,
  });

  return {
    data: query.data ?? [],
    username,
    fetching: query.isFetching,
  };
}