import { useEffect, useRef } from 'react';
import { Outlet, useLocation } from 'react-router';

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
  const location = useLocation();
  const contentRef = useRef<HTMLElement | null>(null);
  const previousLocation = useRef(location);

  useEffect(() => {
    const previous = previousLocation.current;
    previousLocation.current = location;

    const isPathChange = previous.pathname !== location.pathname;
    const isTabChange =
      !isPathChange &&
      new URLSearchParams(previous.search).get('tab') !==
        new URLSearchParams(location.search).get('tab');

    if (!isPathChange && !isTabChange) {
      return;
    }

    window.scrollTo(0, 0);
    contentRef.current?.scrollTo(0, 0);
  }, [location]);

  return (
    <SettingsProvider>
      <MobileNavProvider>
        <div className="app-container">
          <Navbar />
          <EmailVerificationBanner />
          <div className="main-wrapper">
            <Sidebar />
            <main className="content" ref={contentRef}>
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
