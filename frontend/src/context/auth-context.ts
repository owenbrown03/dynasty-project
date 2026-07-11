import { createContext } from 'react';

export type AuthContextType = {
  isOpen: boolean;
  view: 'login' | 'register';
  open: () => void;
  close: () => void;
  switchView: () => void;
};

export const AuthContext =
  createContext<AuthContextType | null>(null);
