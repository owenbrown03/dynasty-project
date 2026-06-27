import { createContext, useContext } from 'react';
import { useBootstrap } from '@/hooks/useBootstrap';
import type { Bootstrap } from '@/types';

type BootstrapContextType = {
  bootstrap: Bootstrap | undefined;
  isLoading: boolean;
};

const BootstrapContext = createContext<BootstrapContextType | null>(null);

export function BootstrapProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const query = useBootstrap();

  return (
    <BootstrapContext.Provider
      value={{
        bootstrap: query.data,
        isLoading: query.isLoading,
      }}
    >
      {children}
    </BootstrapContext.Provider>
  );
}

export function useBootstrapContext() {
  const context = useContext(BootstrapContext);

  if (!context) {
    throw new Error(
      'useBootstrapContext must be used within BootstrapProvider'
    );
  }

  return context;
}