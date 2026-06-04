import { type AxiosInstance } from 'axios';
import { type SendCodeRequest, type VerifyCodeRequest } from '@/types';

export const authEndpoints = (
  client: AxiosInstance,
  prefix: string,
) => ({
  sendCode: (payload: SendCodeRequest) =>
    client.post(`${prefix}/send-code`, payload),

  verifyCode: (payload: VerifyCodeRequest) =>
    client.post(`${prefix}/verify-code`, payload),
});