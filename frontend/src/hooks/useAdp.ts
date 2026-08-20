import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type {
  ADPFilters,
  ADPResponse,
} from '@/types';


export function useAdp(
  filters: ADPFilters,
) {
  return useQuery<ADPResponse>({
    queryKey: queryKeys.adp.results(
      filters as Record<string, unknown>,
    ),
    queryFn: async ({ signal }) => {
      const response = await api.adp.get(
        filters,
        signal,
      );
      return response.data;
    },
    placeholderData: (previousData) => previousData,
    staleTime: 5 * 60 * 1000,
  });
}
