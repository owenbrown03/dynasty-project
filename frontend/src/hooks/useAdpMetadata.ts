import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type {
  ADPFilters,
  ADPMetadataResponse,
} from '@/types';


export function useAdpMetadata(
  filters: ADPFilters,
) {
  return useQuery<ADPMetadataResponse>({
    queryKey: queryKeys.adp.metadata(
      filters as Record<string, unknown>,
    ),
    queryFn: async () => {
      const response = await api.adp.getMetadata(
        filters,
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}
