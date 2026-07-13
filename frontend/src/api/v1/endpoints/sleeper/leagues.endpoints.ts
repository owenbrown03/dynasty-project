import { type AxiosInstance } from 'axios';

import type {
  LeagueOverview,
  LeagueDetails,
  Dashboard,
  LeagueVisibilityItem,
  LeagueVisibilityUpdate,
} from '@/types';

export const leaguesEndpoints = (
  client: AxiosInstance,
  prefix: string
) => ({

  getOverview: (
    username: string,
    includeHidden = false,
  ) =>
    client.get<LeagueOverview[]>(
      `${prefix}/overview/${username}`,
      {
        params: {
          include_hidden: includeHidden,
        },
      },
    ),


  getDetails: (
    league_id: string
  ) =>
    client.get<LeagueDetails>(
      `${prefix}/details/${league_id}`
    ),


  getDashboard: (
    username: string
  ) =>
    client.get<Dashboard>(
      `${prefix}/dashboard/${username}`
    ),

  setVisibility: (
    leagueId: string,
    payload: LeagueVisibilityUpdate,
  ) =>
    client.put<LeagueVisibilityItem>(
      `${prefix}/visibility/${leagueId}`,
      payload,
    ),

});
