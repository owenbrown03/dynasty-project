import { useContext } from 'react';

import { BootstrapContext } from '@/context/bootstrap-context';

export function useBootstrapContext() {
  const context = useContext(BootstrapContext);

  if (!context) {
    throw new Error(
      'useBootstrapContext must be used within BootstrapProvider'
    );
  }

  return context;
}
