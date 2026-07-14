import { type AxiosInstance } from 'axios';

import type {
  AccentColor,
  DraftPickProjectionSettings,
  EmailVerificationConfirmRequest,
  EmailVerificationRequestResponse,
  Login,
  ThemePreference,
  ValueBasis,
  WarValueSettings,
} from '@/types/index';

export const authEndpoints = (client: AxiosInstance, prefix: string) => ({
  register: (credentials: Login) => client.post(`${prefix}/register`, credentials),
  login: (credentials: Login) => client.post(`${prefix}/login`, credentials),
  logout: () => client.post(`${prefix}/logout`),
  resendVerificationEmail: () => client.post<EmailVerificationRequestResponse>(
    `${prefix}/email/resend`,
  ),
  verifyEmail: (body: EmailVerificationConfirmRequest) => (
    client.post(`${prefix}/email/verify`, body)
  ),
  updateThemePreference: (
    theme_preference: ThemePreference,
  ) => client.post(
    `${prefix}/theme`,
    { theme_preference },
  ),
  updateAccentColor: (
    accent_color: AccentColor,
  ) => client.post(
    `${prefix}/accent-color`,
    { accent_color },
  ),
  updateValuePreference: (
    value_preference: ValueBasis,
  ) => client.post(
    `${prefix}/value`,
    { value_preference },
  ),
  updateWarValueSettings: (
    settings: WarValueSettings,
  ) => client.post(
    `${prefix}/war-value`,
    { settings },
  ),
  updateDraftPickProjectionSettings: (
    settings: DraftPickProjectionSettings,
  ) => client.post(
    `${prefix}/draft-pick-projection`,
    { settings },
  ),
});
