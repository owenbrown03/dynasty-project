import { useState } from 'react';

import { api } from '@/api/v1/endpoints';

export const useAuth = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  const openAuth = () => setIsAuthModalOpen(true);
  const closeAuth = () => setIsAuthModalOpen(false);

  const logout = async () => {
    await api.auth.logout();
    setIsLoggedIn(false);
  };

  return {
    isLoggedIn,
    openAuth,
    closeAuth,
    logout,
    isAuthModalOpen,
  };
};