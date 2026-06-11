import { type AxiosInstance } from 'axios';
import { type TradeRequest, type WaiverRequest } from '@/types';

export const writeEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  proposeTrade: async (payload: TradeRequest) => {
    const res = await client.post(`${prefix}/trades/propose`, payload);
    return res.data;
  },

  submitWaiverClaim: async (payload: WaiverRequest) => {
    const res = await client.post(`${prefix}/waivers/claim`, payload);
    return res.data;
  },
});