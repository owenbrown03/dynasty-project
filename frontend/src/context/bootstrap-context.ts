import { createContext } from 'react';

import type { Bootstrap } from '@/types';

export type BootstrapContextType = {
  bootstrap: Bootstrap | undefined;
  isLoading: boolean;
};

export const BootstrapContext =
  createContext<BootstrapContextType | null>(null);
