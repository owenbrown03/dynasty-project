import axios from 'axios';
import { resolveApiBaseUrl } from '@/api/v1/base-url';

export const client = axios.create({
  baseURL: resolveApiBaseUrl(
    typeof window !== 'undefined'
      ? window.location.origin
      : undefined,
  ),
  withCredentials: true,
});