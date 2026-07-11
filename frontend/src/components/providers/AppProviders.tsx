import { QueryClientProvider } from '@tanstack/react-query';

import { appQueryClient } from '@/api/query-client';
import { BootstrapProvider } from '@/context/BootstrapContext';
import { AuthProvider } from '@/context/AuthContext';
import { SleeperAuthProvider } from '@/context/SleeperAuthContext';
import { ThemeProvider } from '@/context/ThemeContext';

export const AppProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={appQueryClient}>
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
