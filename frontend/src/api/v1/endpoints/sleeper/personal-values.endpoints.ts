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
    signal?: AbortSignal,
  ) => client.get<PersonalValueSearchResult[]>(
    `${prefix}/search`,
    {
      params: {
        query,
        league_id: leagueId,
      },
      signal,
    },
  ),
  getPool: (
    leagueId: string,
    signal?: AbortSignal,
  ) => client.get<PersonalValuePoolResponse>(
    `${prefix}/pool`,
    {
      params: {
        league_id: leagueId,
      },
      signal,
    },
  ),
  getPlayer: (
    leagueId: string,
    playerId: string,
    signal?: AbortSignal,
  ) => client.get<PersonalValueDetail>(
    `${prefix}/player/${playerId}`,
    {
      params: {
        league_id: leagueId,
      },
      signal,
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
