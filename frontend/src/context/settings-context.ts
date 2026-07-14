import { createContext } from 'react';

export type SettingsContextType = {
  isOpen: boolean;
  open: () => void;
  close: () => void;
};

export const SettingsContext =
  createContext<SettingsContextType | null>(null);
