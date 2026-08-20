import { useContext } from 'react';
import { MobileNavContext, type MobileNavState } from '@/context/MobileNavContext';

export type { MobileNavState };

export function useMobileNav(): MobileNavState {
  return useContext(MobileNavContext);
}
