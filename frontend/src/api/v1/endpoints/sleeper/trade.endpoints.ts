import { type AxiosInstance } from 'axios';

import type {
  BulkTradeAvailabilityRequest,
  Transaction,
  BulkTradeAvailabilityResponse,
  BulkTradePlayerSearchResult,
  BulkTradeProposalRequest,
  BulkTradeProposalResponse,
  TradeCalculatorPickValueResponse,
} from '@/types';

export const tradeEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  syncLeaguemates: (username: string) =>
    client.post(`${prefix}/${username}/sync-leaguemates`),

  getTradeSignals: (
    username: string,
    signal?: AbortSignal,
  ) =>
    client.get<Transaction[]>(
      `${prefix}/${username}/trade-signals`,
      { signal },
    ),

  searchBulkPlayers: (
    query: string,
    signal?: AbortSignal,
  ) => client.get<BulkTradePlayerSearchResult[]>(
    `${prefix}/bulk/search`,
    {
      params: {
        q: query,
      },
      signal,
    },
  ),

  getBulkAvailability: (
    payload: BulkTradeAvailabilityRequest,
    signal?: AbortSignal,
  ) => client.post<BulkTradeAvailabilityResponse>(
    `${prefix}/bulk/availability`,
    payload,
    { signal },
  ),

  submitBulkOffers: (
    payload: BulkTradeProposalRequest,
  ) => client.post<BulkTradeProposalResponse>(
    `${prefix}/bulk/propose`,
    payload,
  ),

  getTradeCalculatorPickValue: (
    season: string,
    round: number,
    slot: number | null,
    totalRosters: number,
    numQbs: number,
    ppr: number,
    signal?: AbortSignal,
  ) => client.get<TradeCalculatorPickValueResponse>(
    `${prefix}/calculator/pick-value`,
    {
      params: {
        season,
        round,
        slot,
        total_rosters: totalRosters,
        num_qbs: numQbs,
        ppr,
      },
      signal,
    },
  ),
});
