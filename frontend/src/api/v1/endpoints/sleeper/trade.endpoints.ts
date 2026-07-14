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

  getTradeSignals: (username: string) =>
    client.get<Transaction[]>(`${prefix}/${username}/trade-signals`),

  searchBulkPlayers: (
    query: string,
  ) => client.get<BulkTradePlayerSearchResult[]>(
    `${prefix}/bulk/search`,
    {
      params: {
        q: query,
      },
    },
  ),

  getBulkAvailability: (
    payload: BulkTradeAvailabilityRequest,
  ) => client.post<BulkTradeAvailabilityResponse>(
    `${prefix}/bulk/availability`,
    payload,
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
    },
  ),
});
