import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { queryKeys } from '@/api/query-keys';
import type {
  AuctionDraftCenter,
  ValueBasis,
} from '@/types';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';


export function useAuctionDraftCenter(
  draftId: string | undefined,
  valueBasis: ValueBasis,
  search: string,
  page: number,
  pageSize: number,
) {
  const { username } = useSleeperConnection();

  const query = useQuery<AuctionDraftCenter>({
    queryKey: queryKeys.drafts.auctionCenter(
      draftId,
      valueBasis,
      search,
      page,
      pageSize,
    ),
    queryFn: async () => {
      if (!draftId) {
        throw new Error('Missing draft id');
      }

      return api.leagues.getAuctionCenter(
        draftId,
        valueBasis,
        search,
        page,
        pageSize,
      ).then((res) => res.data);
    },
    enabled: !!draftId && !!username,
  });

  return {
    data: query.data,
    loading: query.isLoading,
    fetching: query.isFetching,
    error: query.error,
  };
}
