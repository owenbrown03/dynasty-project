import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AppRoutes } from './Routes';
import { SleeperProvider } from './context/SleeperContext.tsx';
import { ApiProvider } from './context/ApiContext.tsx';

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SleeperProvider>
        <ApiProvider>
          <Toaster position="bottom-right" />
          <AppRoutes />
        </ApiProvider>
      </SleeperProvider>
    </QueryClientProvider>
  );
}