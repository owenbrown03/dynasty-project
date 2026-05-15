import { createContext, useContext } from 'react';

export interface UsernameContextValue {
  username: string;
  setUsername: (username: string) => void;
}

export const UsernameContext = createContext<UsernameContextValue | undefined>(undefined);

export function useUsername() {
  const context = useContext(UsernameContext);
  if (context === undefined) {
    throw new Error('useUsername must be used within a UsernameProvider');
  }
  return context;
}
