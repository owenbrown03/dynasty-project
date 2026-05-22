import { Toaster } from 'react-hot-toast';

import { AppRoutes } from './Routes';
import { UserProvider } from './context/UserContext.tsx';
import { ApiProvider } from './context/ApiContext.tsx';

export function App() {
  return (
    <UserProvider>
      <ApiProvider>
        <Toaster position="bottom-right" />
        <AppRoutes />
      </ApiProvider>
    </UserProvider>
  );
}