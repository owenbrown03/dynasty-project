import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type {
  RookieWarHistory,
} from '@/types';


export function useRookieWarHistory(
  leagueId?: string,
  enabled: boolean = true,
) {
  return useQuery<RookieWarHistory>({
    queryKey: queryKeys.leagues.rookieWarHistory(
      leagueId,
    ),
    queryFn: async ({ signal }) => {
      const response = await api.leagues.getRookieWarHistory(
        leagueId,
        undefined,
        signal,
      );
      return response.data;
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}
