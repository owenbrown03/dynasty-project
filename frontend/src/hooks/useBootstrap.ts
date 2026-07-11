import { useQuery } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type { Bootstrap } from '@/types';

export function useBootstrap() {
  return useQuery<Bootstrap>({
    queryKey: BOOTSTRAP_QUERY_KEY,
    queryFn: async () => {
      return api.bootstrap.bootstrap();
    },
    staleTime: 5 * 60 * 1000,
  });
}
