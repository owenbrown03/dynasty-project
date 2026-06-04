import { type AxiosInstance } from 'axios';
import { type TradeRequest, type WaiverRequest } from '@/types';

export const writeEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  proposeTrade: (payload: TradeRequest) =>
    client.post(`${prefix}/trades/propose`, payload),

  submitWaiverClaim: (payload: WaiverRequest) =>
    client.post(`${prefix}/waivers/claim`, payload),
});