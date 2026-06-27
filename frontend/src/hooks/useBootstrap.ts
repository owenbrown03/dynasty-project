import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import type { Bootstrap } from '@/types';

const KEY = ['bootstrap'] as const;

export function useBootstrap() {

  return useQuery<Bootstrap>({
    queryKey: KEY,
    queryFn: async () => {
      return api.bootstrap.bootstrap();
    },
    staleTime: 5 * 60 * 1000,
  });
}