import { type AxiosInstance } from 'axios';

import type {
  ADPFilters,
  ADPMetadataResponse,
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
  getMetadata: (
    filters: ADPFilters,
  ) =>
    client.get<ADPMetadataResponse>(
      `${prefix}/metadata`,
      {
        params: filters,
      },
    ),
});
