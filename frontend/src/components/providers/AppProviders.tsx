import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AuthProvider } from '@/context/AuthContext';
import { SleeperAuthProvider } from '@/context/SleeperAuthContext';

const queryClient = new QueryClient();

export const AppProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SleeperAuthProvider>
          {children}
        </SleeperAuthProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};