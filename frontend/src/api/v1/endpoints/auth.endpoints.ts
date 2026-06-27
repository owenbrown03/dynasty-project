import { type AxiosInstance } from 'axios';

import type { Login } from '@/types/index';

export const authEndpoints = (client: AxiosInstance, prefix: string) => ({
  register: (credentials: Login) => client.post(`${prefix}/register`, credentials),
  login: (credentials: Login) => client.post(`${prefix}/login`, credentials),
  logout: () => client.post(`${prefix}/logout`),
});