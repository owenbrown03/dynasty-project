import { useState } from 'react';

import {
  AuthContext,
  type AuthContextType,
} from '@/context/auth-context';

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
