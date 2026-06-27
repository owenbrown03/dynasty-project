import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { BootstrapProvider } from '@/context/BootstrapContext';
import { AuthProvider } from '@/context/AuthContext';
import { SleeperAuthProvider } from '@/context/SleeperAuthContext';

const queryClient = new QueryClient();

export const AppProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <BootstrapProvider>
        <AuthProvider>
          <SleeperAuthProvider>
            {children}
          </SleeperAuthProvider>
        </AuthProvider>
      </BootstrapProvider>
    </QueryClientProvider>
  );
};