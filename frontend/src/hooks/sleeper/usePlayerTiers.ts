import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type {
  TierBoard,
  ValueBasis,
} from '@/types';
import { useBootstrap } from '@/hooks/useBootstrap';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';


export function usePlayerTiers(
  valueBasis: ValueBasis,
  leagueId?: string,
  enabled: boolean = true,
  cheap = false,
) {
  const bootstrap = useBootstrap();
  const connection = useSleeperConnection();
  const viewerKey = JSON.stringify({
    authenticated: bootstrap.data?.authenticated ?? false,
    siteUserId: bootstrap.data?.site_user?.id ?? null,
    sleeperUserId: connection.connection?.sleeper_user_id ?? null,
  });

  const query = useQuery<TierBoard>({
    queryKey: queryKeys.players.tiers(
      valueBasis,
      leagueId,
      viewerKey,
      cheap,
    ),
    queryFn: async ({ signal }) => {
      return api.players
        .getTiers(
          valueBasis,
          leagueId,
          cheap,
          signal,
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
