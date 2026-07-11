import { QueryClientProvider } from '@tanstack/react-query';

import { appQueryClient } from '@/api/query-client';
import { BootstrapProvider } from '@/context/BootstrapContext';
import { AuthProvider } from '@/context/AuthContext';
import { SleeperAuthProvider } from '@/context/SleeperAuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import { ValuePreferenceProvider } from '@/context/ValuePreferenceContext';

export const AppProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={appQueryClient}>
      <BootstrapProvider>
        <ThemeProvider>
          <ValuePreferenceProvider>
            <AuthProvider>
              <SleeperAuthProvider>
                {children}
              </SleeperAuthProvider>
            </AuthProvider>
          </ValuePreferenceProvider>
        </ThemeProvider>
      </BootstrapProvider>
    </QueryClientProvider>
  );
};
