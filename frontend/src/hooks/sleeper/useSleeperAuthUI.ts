import { useState } from 'react';

export const useSleeperAuthUI = () => {
  const [isOpen, setIsOpen] = useState(false);

  return {
    isAuthModalOpen: isOpen,
    openAuth: () => setIsOpen(true),
    closeAuth: () => setIsOpen(false),
  };
};