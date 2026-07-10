import { type AxiosInstance } from 'axios';

import type {
  Login,
  ThemePreference,
} from '@/types/index';

export const authEndpoints = (client: AxiosInstance, prefix: string) => ({
  register: (credentials: Login) => client.post(`${prefix}/register`, credentials),
  login: (credentials: Login) => client.post(`${prefix}/login`, credentials),
  logout: () => client.post(`${prefix}/logout`),
  updateThemePreference: (
    theme_preference: ThemePreference,
  ) => client.post(
    `${prefix}/theme`,
    { theme_preference },
  ),
});
