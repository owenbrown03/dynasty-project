import { type AxiosInstance } from 'axios';

import type {
  LeagueOverview,
  LeagueDetails,
  Dashboard
} from '@/types';

export const leaguesEndpoints = (
  client: AxiosInstance,
  prefix: string
) => ({

  getOverview: (
    username: string
  ) =>
    client.get<LeagueOverview[]>(
      `${prefix}/overview/${username}`
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

});