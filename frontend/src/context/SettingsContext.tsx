import { useState } from 'react';

import {
  SettingsContext,
  type SettingsContextType,
} from '@/context/settings-context';

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setOpen] = useState(false);

  const value: SettingsContextType = {
    isOpen,
    open: () => setOpen(true),
    close: () => setOpen(false),
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}
