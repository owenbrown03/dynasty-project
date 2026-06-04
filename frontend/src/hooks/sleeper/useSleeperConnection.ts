import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/v1/endpoints';

export function useUpsertSleeper() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: api.connection.upsert,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sleeper-connection'] });
    },
  });
}

export function useSleeperConnection() {
  return useQuery({
    queryKey: ['sleeper-connection'],
    queryFn: api.connection.get,
  });
}

export function useSleeperState() {
  const { data, ...rest } = useSleeperConnection();

  return {
    ...rest,
    connection: data,

    sleeperUsername: data?.username,
    isSleeperLinked: !!data?.sleeper_id,
    isSleeperAuthed: !!data?.can_write,
    canRead: !!data?.can_read,
    canWrite: !!data?.can_write,
  };
}