import { type AxiosInstance } from 'axios';

export const playerEndpoints = (client: AxiosInstance, prefix: string) => ({
  sync: () => client.post(`${prefix}/sync`),
});