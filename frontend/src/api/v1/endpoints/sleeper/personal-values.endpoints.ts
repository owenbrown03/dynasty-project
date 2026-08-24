import { type AxiosInstance } from 'axios';

import type {
  PersonalValueDetail,
  PersonalValueRankingsResetRequest,
  PersonalValueRankingsResetResponse,
  PersonalValueRankingsResponse,
  PersonalValueRankingsUpdateRequest,
  PersonalValueRankingsUpdateResponse,
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
  getRankings: (
    leagueId: string,
    position: string,
    scope: string,
    signal?: AbortSignal,
  ) => client.get<PersonalValueRankingsResponse>(
    `${prefix}/rankings`,
    {
      params: {
        league_id: leagueId,
        position,
        scope,
      },
      signal,
    },
  ),
  saveRankings: (
    payload: PersonalValueRankingsUpdateRequest,
  ) => client.post<PersonalValueRankingsUpdateResponse>(
    `${prefix}/rankings`,
    payload,
    { timeout: 120000 },
  ),
  resetRankings: (
    payload: PersonalValueRankingsResetRequest,
  ) => client.post<PersonalValueRankingsResetResponse>(
    `${prefix}/rankings/reset`,
    payload,
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
