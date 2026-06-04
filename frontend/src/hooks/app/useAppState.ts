import { useAuth } from '@/hooks/auth/useAuth';
import { useSleeperConnection } from '@/hooks/sleeper/useSleeperConnection';
import { type AppAccessState } from '@/types/appState';

export const useAppState = () => {
  const auth = useAuth();
  const { data: sleeper } = useSleeperConnection();

  let state: AppAccessState = 'anonymous';

  if (auth.isLoggedIn) {
    if (!sleeper?.username) {
      state = 'authenticated-no-sleeper';
    } else if (sleeper.isWriteEnabled) {
      state = 'sleeper-write';
    } else {
      state = 'sleeper-read-only';
    }
  }

  return {
    state,
    auth,
    sleeper,
  };
};