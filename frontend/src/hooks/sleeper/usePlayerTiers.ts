import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import type {
  TierBoard,
  ValueBasis,
} from '@/types';


export function usePlayerTiers(
  valueBasis: ValueBasis,
  leagueId?: string,
  enabled: boolean = true,
) {
  const query = useQuery<TierBoard>({
    queryKey: [
      'player-tiers',
      valueBasis,
      leagueId ?? null,
    ],
    queryFn: async () => {
      return api.players
        .getTiers(
          valueBasis,
          leagueId,
        )
        .then((res) => res.data);
    },
    enabled,
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}
