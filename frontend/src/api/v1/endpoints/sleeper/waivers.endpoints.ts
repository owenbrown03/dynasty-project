import type { AxiosInstance } from 'axios';

import type {
  ValueBasis,
  WaiverAvailablePlayersResponse,
  WaiverClaimRequest,
  WaiverClaimResponse,
  WaiverLeagueOption,
  WaiverOverviewResponse,
  WaiverRosterPlayersResponse,
  BulkWaiverAvailabilityResponse,
  BulkWaiverClaimRequest,
  BulkWaiverClaimResponse,
  BulkWaiverPlayerSearchResult,
  WaiverRecentlyDroppedResponse,
} from '@/types';


export const waiversEndpoints = (
  client: AxiosInstance,
  basePath: string,
) => ({
  getOverview: (
    valueBasis: ValueBasis,
    signal?: AbortSignal,
  ) => {
    return client.get<WaiverOverviewResponse>(
      `${basePath}/overview`,
      {
        params: {
          value_basis: valueBasis,
        },
        signal,
      },
    );
  },

  getRecentDrops: (
    valueBasis: ValueBasis,
    page: number,
    pageSize: number,
    sortBy: 'value' | 'recency',
    cheap = false,
    signal?: AbortSignal,
  ) => {
    return client.get<WaiverRecentlyDroppedResponse>(
      `${basePath}/recent-drops`,
      {
        params: {
          value_basis: valueBasis,
          page,
          page_size: pageSize,
          sort_by: sortBy,
          cheap,
        },
        signal,
      },
    );
  },

  getLeagues: (
    signal?: AbortSignal,
  ) => {
    return client.get<WaiverLeagueOption[]>(
      `${basePath}/leagues`,
      { signal },
    );
  },

  getAvailablePlayers: (
    leagueId: string | undefined,
    valueBasis: ValueBasis,
    page: number,
    pageSize: number,
    signal?: AbortSignal,
  ) => {
    return client.get<WaiverAvailablePlayersResponse>(
      `${basePath}/available`,
      {
        params: {
          league_id: leagueId,
          value_basis: valueBasis,
          page,
          page_size: pageSize,
        },
        signal,
      },
    );
  },

  submitClaim: (
    payload: WaiverClaimRequest,
  ) => {
    return client.post<WaiverClaimResponse>(
      `${basePath}/claim`,
      payload,
    );
  },

  getRosterPlayers: (
    leagueId: string,
    valueBasis: ValueBasis,
    signal?: AbortSignal,
  ) => {
    return client.get<WaiverRosterPlayersResponse>(
      `${basePath}/roster-players`,
      {
        params: {
          league_id: leagueId,
          value_basis: valueBasis,
        },
        signal,
      },
    );
  },

  searchBulkPlayers: (
    query: string,
    signal?: AbortSignal,
  ) => {
    return client.get<BulkWaiverPlayerSearchResult[]>(
      `${basePath}/bulk/search`,
      {
        params: {
          q: query,
        },
        signal,
      },
    );
  },

  getBulkAvailability: (
    playerId: string,
    valueBasis: ValueBasis,
    signal?: AbortSignal,
  ) => {
    return client.get<BulkWaiverAvailabilityResponse>(
      `${basePath}/bulk/availability`,
      {
        params: {
          player_id: playerId,
          value_basis: valueBasis,
        },
        signal,
      },
    );
  },

  submitBulkClaims: (
    payload: BulkWaiverClaimRequest,
  ) => {
    return client.post<BulkWaiverClaimResponse>(
      `${basePath}/bulk/claim`,
      payload,
    );
  },

});
