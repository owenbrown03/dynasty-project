import { Toaster } from 'react-hot-toast';

import { AppRoutes } from './Routes';
import { AppProviders } from '@/components/providers/AppProviders';

export function App() {
  return (
    <AppProviders>
      <Toaster position="bottom-right" />
      <AppRoutes />
    </AppProviders>
  );
}