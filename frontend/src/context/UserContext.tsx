import { createContext, useContext, useState, type ReactNode } from 'react';

interface UserContextType {
  username: string | null;
  setUsername: (username: string | null) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null);

  return (
    <UserContext.Provider value={{ username, setUsername }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUserContext() {
  const context = useContext(UserContext);
  
  if (context === undefined) {
    throw new Error('useUserContext must be used within a UserProvider framework');
  }
  
  return context;
}