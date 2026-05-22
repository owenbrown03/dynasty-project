import { type AxiosInstance } from 'axios';

import { type Transaction } from '@/types';

export const tradeEndpoints = (client: AxiosInstance, prefix: string) => ({
  syncLeaguemates: (username: string) => client.post(`${prefix}/${username}/sync-leaguemates`),
  getTradeSignals: (username: string) => client.get<Transaction[]>(`${prefix}/${username}/trade-signals`),
});