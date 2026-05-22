import { type AxiosInstance } from 'axios';

import { type Roster, type Orphan } from '@/types';

export const userEndpoints = (client: AxiosInstance, prefix: string) => ({
  sync: (username: string) => client.post(`${prefix}/${username}/sync`),
  getRosters: (username: string) => client.get<Roster[]>(`${prefix}/${username}/rosters`),
  getOrphans: (username: string) => client.get<Orphan[]>(`${prefix}/${username}/orphans`),
});