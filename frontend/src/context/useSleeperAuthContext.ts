import { useContext } from 'react';

import { SleeperAuthContext } from '@/context/sleeper-auth-context';

export function useSleeperAuthContext() {
  const context = useContext(SleeperAuthContext);

  if (!context) {
    throw new Error(
      'useSleeperAuthContext must be used within SleeperAuthProvider'
    );
  }

  return context;
}
