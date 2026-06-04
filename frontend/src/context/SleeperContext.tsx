import { createContext, useContext, useState, type ReactNode } from 'react';

interface SleeperContextType {
  sleeperUsername: string | undefined;
  setSleeperUsername: (username: string | undefined) => void;
  sleeperToken: string | undefined;
  setSleeperToken: (username: string | undefined) => void;
}

const SleeperContext = createContext<SleeperContextType | undefined>(undefined);

export function SleeperProvider({ children }: { children: ReactNode }) {
  const [sleeperUsername, setSleeperUsername] = useState<string | undefined>(undefined);
  const [sleeperToken, setSleeperToken] = useState<string | undefined>(undefined);
  
  return (
    <SleeperContext.Provider value={{ sleeperUsername, setSleeperUsername, sleeperToken, setSleeperToken }}>
      {children}
    </SleeperContext.Provider>
  );
}

export function useSleeperContext() {
  const context = useContext(SleeperContext);
  
  if (context === undefined) {
    throw new Error('useSleeperContext must be used within a UserProvider framework');
  }
  
  return context;
}