import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/v1/endpoints';

export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: api.auth.validate,
  });
}