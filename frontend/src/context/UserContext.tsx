import { createContext, useContext, useState, type ReactNode } from 'react';

interface UserContextType {
  username: string | undefined;
  setUsername: (username: string | undefined) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | undefined>(undefined);
  
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