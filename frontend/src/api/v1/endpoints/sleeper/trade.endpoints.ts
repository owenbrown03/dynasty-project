import { type AxiosInstance } from 'axios';

import type {
  Transaction,
  BulkTradeAvailabilityResponse,
  BulkTradePlayerSearchResult,
  BulkTradeProposalRequest,
  BulkTradeProposalResponse,
  TradeDirection,
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
    playerId: string,
    direction: TradeDirection,
    pickSeason: string,
    pickRound: number,
  ) => client.get<BulkTradeAvailabilityResponse>(
    `${prefix}/bulk/availability`,
    {
      params: {
        player_id: playerId,
        direction,
        pick_season: pickSeason,
        pick_round: pickRound,
      },
    },
  ),

  submitBulkOffers: (
    payload: BulkTradeProposalRequest,
  ) => client.post<BulkTradeProposalResponse>(
    `${prefix}/bulk/propose`,
    payload,
  ),
});