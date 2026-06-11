import { type AxiosInstance } from 'axios';

import type { Login, MeRequest } from '@/types/index';

export const authEndpoints = (client: AxiosInstance, prefix: string) => ({
  register: (credentials: Login) => client.post(`${prefix}/register`, credentials),
  login: (credentials: Login) => client.post(`${prefix}/login`, credentials),
  logout: () => client.post(`${prefix}/logout`),
  validate: () => client.post(`${prefix}/validate`),
  me: async (): Promise<MeRequest> => {
      const res = await client.get<MeRequest>(`${prefix}/me`);
      return res.data;
    },
});