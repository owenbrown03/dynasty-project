import { type AxiosInstance } from 'axios';

import type {
  ADPFilters,
  ADPResponse,
} from '@/types';


export const adpEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  get: (
    filters: ADPFilters,
  ) =>
    client.get<ADPResponse>(
      `${prefix}`,
      {
        params: filters,
      },
    ),
});
