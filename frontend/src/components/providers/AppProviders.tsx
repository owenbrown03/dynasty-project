import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { BootstrapProvider } from '@/context/BootstrapContext';
import { AuthProvider } from '@/context/AuthContext';
import { SleeperAuthProvider } from '@/context/SleeperAuthContext';
import { ThemeProvider } from '@/context/ThemeContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 30 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});

export const AppProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <BootstrapProvider>
        <ThemeProvider>
          <AuthProvider>
            <SleeperAuthProvider>
              {children}
            </SleeperAuthProvider>
          </AuthProvider>
        </ThemeProvider>
      </BootstrapProvider>
    </QueryClientProvider>
  );
};
