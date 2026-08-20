import { type AxiosInstance } from 'axios';
import type {
  TierBoard,
  ValueBasis,
} from '@/types';

export const playerEndpoints = (client: AxiosInstance, prefix: string) => ({
  sync: () => client.post(`${prefix}/sync`),
  getTiers: (
    valueBasis: ValueBasis,
    leagueId?: string,
    signal?: AbortSignal,
  ) =>
    client.get<TierBoard>(
      `${prefix}/tiers`,
      {
        params: {
          value_basis: valueBasis,
          league_id: leagueId,
        },
        signal,
      },
    ),
});
