import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/v1/endpoints';

export function useLogout() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: api.auth.logout,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['user'] });
      qc.invalidateQueries({ queryKey: ['sleeper-connection'] });
    },
  });
}