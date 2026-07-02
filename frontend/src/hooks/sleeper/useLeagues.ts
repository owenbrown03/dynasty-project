import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import type {
  LeagueOverview,
  LeagueDetails,
  Dashboard
} from '@/types';

import { useSleeperConnection } from '@/hooks/sleeper/useConnection';


export function useLeagueOverview() {

  const { username } = useSleeperConnection();

  const query = useQuery<LeagueOverview[]>({
    queryKey: [
      'league-overview',
      username
    ],

    queryFn: async () => {

      if (!username)
        throw new Error(
          'Missing username'
        );

      return api.leagues
        .getOverview(username)
        .then(res => res.data);

    },

    enabled: !!username,
  });

  return {
    data: query.data ?? [],
    username,
    loading: query.isLoading,
    fetching: query.isFetching,
  };

}


export function useLeagueDetails(league_id?: string) {

  const query = useQuery<LeagueDetails>({

    queryKey: [
      'league-details',
      league_id
    ],

    queryFn: async () => {

      if (!league_id)
        throw new Error(
          'Missing league id'
        );

      return api.leagues
        .getDetails(league_id)
        .then(res => res.data);

    },

    enabled: !!league_id,

  });

  return {

    data: query.data,

    loading: query.isLoading,

    fetching: query.isFetching,

  };

}


export function useLeagueDashboard() {

  const {
    username
  } = useSleeperConnection();

  const query = useQuery<Dashboard>({

    queryKey:[
      'league-dashboard',
      username
    ],

    queryFn: async()=>{

      if(!username)
        throw new Error(
          'Missing username'
        );

      return api.leagues
        .getDashboard(username)
        .then(res=>res.data);

    },

    enabled:!!username,

  });

  return {
    data: query.data,
    username,
    loading: query.isLoading,
    fetching: query.isFetching,
  };

}