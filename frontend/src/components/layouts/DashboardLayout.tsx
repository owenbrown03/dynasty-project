import { useState, useEffect } from 'react';
import { Outlet } from 'react-router';

import './DashboardLayout.css';
import { Navbar } from './Navbar.tsx'; 
import { Sidebar } from './Sidebar.tsx';  
import { AuthModal } from '../auth/AuthModal.tsx';
import { api } from '@/api/v1/endpoints';
import { useMutation } from '@/hooks/useMutation';
import { useUserContext } from '../../context/UserContext';
import { notify } from '@/utils/notify';

export const DashboardLayout = () => {
  const { username, setUsername } = useUserContext();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [pendingSync, setPendingSync] = useState<string | null>(null);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await api.auth.validate();
        if (response.data?.authenticated) {
          setIsLoggedIn(true);
        }
      } catch (err) {
        console.error("Session validation failed:", err);
        setIsLoggedIn(false);
      }
    };

    checkSession();
  }, []);

  const logoutMutation = useMutation('user-logout', api.auth.logout);
  const handleLogout = async () => {
    console.log('Entering handleLogout');
    try {
      await logoutMutation.mutateAsync();
      setIsLoggedIn(false);
      setUsername(undefined);
      console.log('Logout successful');
    } catch (err) {
      notify.error('Logout failed');
    }
  };

  const handleSyncAttempt = (username: string): boolean => {
    console.log('Entering handleSyncAttempt with username:', username);
    if (!isLoggedIn) {
      setPendingSync(username);
      setIsAuthOpen(true);
      return false;
    } else {
      performSync(username);
      return true;
    }
  };

  const syncSleeper = useMutation('sync-sleeper', api.auth.syncSleeper);
  const performSync = async (username: string) => {
    try {
      await syncSleeper.mutateAsync(username);
      setUsername(username);
    } catch (err) {
      notify.error('Sleeper sync failed');
    }
  };

  const getSleeper = useMutation('get-sleeper', api.auth.getSleeper);
  const handleLoginSuccess = async () => {
    console.log('Entering handleLoginSuccess');
    setIsLoggedIn(true);
    setIsAuthOpen(false);
    if (pendingSync) {
      await performSync(pendingSync);
      setPendingSync(null);
    }
    const response = await getSleeper.mutateAsync(); 
    if (response.data?.data?.sleeper_username) {
      setUsername(response.data.data.sleeper_username);
    }
  };

  return (
    <div className="app-container">
      <Navbar 
        onLoginClick={() => setIsAuthOpen(true)}
        isLoggedIn={isLoggedIn}
        onLogoutClick={handleLogout}
        sleeperUsername={username}
      />
      <div className="main-wrapper">
        <Sidebar />
        <main className="content">
          <Outlet 
            context={{ 
              pendingSync,
              handleSyncAttempt
            }}
          />
        </main>
      </div>
      <AuthModal 
        isOpen={isAuthOpen} 
        onClose={() => setIsAuthOpen(false)}
        onLogin={handleLoginSuccess}
      />
    </div>
  );
};