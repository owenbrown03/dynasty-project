import { useContext } from 'react';

import { SettingsContext } from '@/context/settings-context';

export function useSettingsContext() {
  const context = useContext(SettingsContext);

  if (!context) {
    throw new Error('useSettingsContext must be used within SettingsProvider');
  }

  return context;
}
