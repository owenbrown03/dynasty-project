import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type { ADPDatasetReport } from '@/types';


export function useAdpReport() {
  return useQuery<ADPDatasetReport>({
    queryKey: queryKeys.adp.report,
    queryFn: async () => {
      const response = await api.adp.getReport();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}
