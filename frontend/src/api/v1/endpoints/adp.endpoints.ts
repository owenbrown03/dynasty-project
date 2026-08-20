import { type AxiosInstance } from 'axios';

import type {
  ADPDatasetReport,
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
    signal?: AbortSignal,
  ) =>
    client.get<ADPResponse>(
      `${prefix}`,
      {
        params: filters,
        signal,
      },
    ),
  getMetadata: (
    filters: ADPFilters,
    signal?: AbortSignal,
  ) =>
    client.get<ADPMetadataResponse>(
      `${prefix}/metadata`,
      {
        params: filters,
        signal,
      },
    ),
  getReport: (signal?: AbortSignal) =>
    client.get<ADPDatasetReport>(
      `${prefix}/report`,
      { signal },
    ),
});
