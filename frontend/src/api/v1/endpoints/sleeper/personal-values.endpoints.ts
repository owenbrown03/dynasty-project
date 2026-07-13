import { type AxiosInstance } from 'axios';

import type {
  PersonalValueDetail,
  PersonalValuePoolResponse,
  PersonalValueSearchResult,
  PersonalValueUpdateRequest,
} from '@/types';

export const personalValuesEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  search: (
    query: string,
    leagueId?: string,
  ) => client.get<PersonalValueSearchResult[]>(
    `${prefix}/search`,
    {
      params: {
        query,
        league_id: leagueId,
      },
    },
  ),
  getPool: (
    leagueId: string,
  ) => client.get<PersonalValuePoolResponse>(
    `${prefix}/pool`,
    {
      params: {
        league_id: leagueId,
      },
    },
  ),
  getPlayer: (
    leagueId: string,
    playerId: string,
  ) => client.get<PersonalValueDetail>(
    `${prefix}/player/${playerId}`,
    {
      params: {
        league_id: leagueId,
      },
    },
  ),
  savePlayer: (
    leagueId: string,
    playerId: string,
    payload: PersonalValueUpdateRequest,
  ) => client.post<PersonalValueDetail>(
    `${prefix}/player/${playerId}`,
    payload,
    {
      params: {
        league_id: leagueId,
      },
    },
  ),
});
