import { Outlet } from 'react-router';

import './DashboardLayout.css'
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { AuthModal } from '../auth/AuthModal';
import { EmailVerificationBanner } from '../auth/EmailVerificationBanner';
import { SettingsModal } from '../settings/SettingsModal';
import { SettingsProvider } from '@/context/SettingsContext';
import { MobileNavProvider } from '@/context/MobileNavContext';
import { SleeperAuthModal } from '../sleeper/SleeperAuthModal';

export const DashboardLayout = () => {
  return (
    <SettingsProvider>
      <MobileNavProvider>
        <div className="app-container">
          <Navbar />
          <EmailVerificationBanner />
          <div className="main-wrapper">
            <Sidebar />
            <main className="content">
              <Outlet />
            </main>
          </div>
          <AuthModal />
          <SettingsModal />
          <SleeperAuthModal />
        </div>
      </MobileNavProvider>
    </SettingsProvider>
  );
};
