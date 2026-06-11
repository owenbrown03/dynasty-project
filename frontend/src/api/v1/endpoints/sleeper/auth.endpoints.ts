import { type AxiosInstance } from 'axios';
import type { SendCodeResponse, VerifyCodeResponse, SendCodeRequest, VerifyCodeRequest } from '@/types';

export const authEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  sendCode: (payload: SendCodeRequest) =>
    client.post<SendCodeResponse>(`${prefix}/send-code`, payload),

  verifyCode: (payload: VerifyCodeRequest) =>
    client.post<VerifyCodeResponse>(`${prefix}/verify-code`, payload),
});