import { type AxiosInstance } from 'axios';

import type {
  BulkTradeAvailabilityRequest,
  Transaction,
  BulkTradeAvailabilityResponse,
  BulkTradePlayerSearchResult,
  BulkTradeProposalRequest,
  BulkTradeProposalResponse,
  TradeCalculatorPickValueResponse,
  TradeCalculatorWaiverAdjustmentResponse,
} from '@/types';

export const tradeEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  syncLeaguemates: (username: string) =>
    client.post(`${prefix}/${username}/sync-leaguemates`),

  getTradeSignals: (
    username: string,
    cheap = false,
    signal?: AbortSignal,
  ) =>
    client.get<Transaction[]>(
      `${prefix}/${username}/trade-signals`,
      {
        params: { cheap },
        signal,
      },
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

  getTradeCalculatorWaiverAdjustment: (
    totalRosters: number,
    numQbs: number,
    ppr: number,
    myPlayersOut: number,
    theirPlayersOut: number,
    signal?: AbortSignal,
  ) => client.get<TradeCalculatorWaiverAdjustmentResponse>(
    `${prefix}/calculator/waiver-adjustment`,
    {
      params: {
        total_rosters: totalRosters,
        num_qbs: numQbs,
        ppr,
        my_players_out: myPlayersOut,
        their_players_out: theirPlayersOut,
      },
      signal,
    },
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
