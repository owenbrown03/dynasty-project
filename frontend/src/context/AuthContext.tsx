import { useState, useContext, createContext } from 'react';

type AuthContextType = {
  isOpen: boolean;
  view: 'login' | 'register';

  open: () => void;
  close: () => void;
  switchView: () => void;
};

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setOpen] = useState(false);
  const [view, setView] = useState<'login' | 'register'>('login');

  const value: AuthContextType = {
    isOpen,
    view,
    open: () => setOpen(true),
    close: () => setOpen(false),
    switchView: () =>
      setView((v) => (v === 'login' ? 'register' : 'login')),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }

  return context;
}