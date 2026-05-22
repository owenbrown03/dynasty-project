import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

interface ApiProviderProps {
  children: ReactNode;
}

interface ApiContextType {
  isCalling: (key: string) => boolean;
  executeCall: (syncKey: string, apiCallFunction: () => Promise<any>) => Promise<any>;
}

const ApiContext = createContext<ApiContextType | null>(null);

export const ApiProvider = ({ children }: ApiProviderProps) => {
  const [activeCalls, setActiveCalls] = useState<Record<string, boolean>>({});

  const executeCall = useCallback(async (
    syncKey: string, 
    apiCallFunction: () => Promise<any>
  ) => {

    setActiveCalls(prev => {
      if (prev[syncKey]) return prev; // Guard
      return { ...prev, [syncKey]: true };
    });

    try {
      return await apiCallFunction();
    } catch (error) {
      console.error(`[Guard] Api call failed for ${syncKey}:`, error);
      throw error;
    } finally {
      setActiveCalls(prev => ({ ...prev, [syncKey]: false }));
    }
  }, []);

  return (
    <ApiContext.Provider value={{ isCalling: (key: string) => !!activeCalls[key], executeCall }}>
      {children}
    </ApiContext.Provider>
  );
};

export const useApi = (): ApiContextType => {
  const context = useContext(ApiContext);
  if (!context) throw new Error('useApi must be used within an ApiProvider');
  return context;
};