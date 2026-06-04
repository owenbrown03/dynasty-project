import { type AxiosInstance } from 'axios';

export const connectionEndpoints = (client: AxiosInstance, prefix: string) => ({
  get: () => client.get(`${prefix}`),
  upsert: (sleeper_username: string) => client.post(`${prefix}/upsert${sleeper_username}`, sleeper_username),
});