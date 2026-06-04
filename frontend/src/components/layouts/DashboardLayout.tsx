import { Outlet } from 'react-router';

import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { AuthModal } from '../auth/AuthModal';
import { SleeperAuthModal } from '../sleeper/SleeperAuthModal';

import { useAuth } from '@/hooks/auth/useAuth';
import { useSleeperAuth } from '@/hooks/sleeper/useSleeperAuth';

export const DashboardLayout = () => {
  const auth = useAuth();
  const sleeper = useSleeperAuth();

  return (
    <div className="app-container">
      <Navbar
        onSleeperAuthClick={sleeper.openAuth}
      />

      <Sidebar />
      <Outlet />

      <AuthModal
        isOpen={auth.isAuthModalOpen}
        onClose={auth.closeAuth}
      />

      <SleeperAuthModal
        isOpen={sleeper.isAuthModalOpen}
        onClose={sleeper.closeAuth}
      />
    </div>
  );
};