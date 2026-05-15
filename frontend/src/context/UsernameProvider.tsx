import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import { UsernameContext } from './usernameContext';

interface UsernameProviderProps {
  children: ReactNode;
}

export function UsernameProvider({ children }: UsernameProviderProps) {
  const [username, setUsername] = useState('');
  const value = useMemo(() => ({ username, setUsername }), [username]);

  return (
    <UsernameContext.Provider value={value}>
      {children}
    </UsernameContext.Provider>
  );
}
