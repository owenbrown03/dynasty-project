import { type AxiosInstance } from 'axios';

import {
  type CommissionerOrphansResponse,
  type Orphan,
  type Roster,
  type ValueBasis,
} from '@/types';

export const userEndpoints = (client: AxiosInstance, prefix: string) => ({
  sync: (username: string) => client.post(`${prefix}/${username}/sync`),
  getRosters: (username: string) => client.get<Roster[]>(`${prefix}/${username}/rosters`),
  getOrphans: (username: string) => client.get<Orphan[]>(`${prefix}/${username}/orphans`),
  getCommissionerOrphans: (
    username: string,
    valueBasis: ValueBasis,
  ) => client.get<CommissionerOrphansResponse>(
    `${prefix}/${username}/commissioner/orphans`,
    {
      params: {
        value_basis: valueBasis,
      },
    },
  ),
});
