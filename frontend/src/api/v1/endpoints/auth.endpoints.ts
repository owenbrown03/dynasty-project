import { type AxiosInstance } from 'axios';

export const authEndpoints = (client: AxiosInstance, prefix: string) => ({
  register: (credentials: any) => client.post(`${prefix}/register`, credentials),
  login: (credentials: any) => client.post(`${prefix}/login`, credentials),
  logout: () => client.post(`${prefix}/logout`),
  validate: () => client.post(`${prefix}/validate`),
  getSleeper: () => client.get(`${prefix}/sleeper`),
  syncSleeper: (sleeper_username: string) => client.post(`${prefix}/${sleeper_username}/sync-sleeper`, sleeper_username),
});