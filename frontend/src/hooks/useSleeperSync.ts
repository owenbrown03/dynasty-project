import { api } from '@/api/v1/endpoints';
import { useMutation } from '@/hooks/useMutation';

export const useSleeperSync = () => {
  const userSync = useMutation('user-sync', api.users.sync);
  const mateSync = useMutation('mate-sync', api.trades.syncLeaguemates);
  
  const performSync = async (username: string) => {
    return await Promise.all([
      userSync.mutateAsync(username),
      mateSync.mutateAsync(username),
    ]);
  };

  return { performSync, isSyncing: userSync.loading || mateSync.loading };
};