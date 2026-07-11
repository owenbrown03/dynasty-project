import { createContext } from 'react';

export type SleeperAuthStep = 'send' | 'verify';

export type SleeperAuthContextType = {
  isOpen: boolean;
  step: SleeperAuthStep;
  username: string | null;
  captcha: string | null;
  setCaptcha: (token: string | null) => void;
  setStep: (step: SleeperAuthStep) => void;
  setUsername: (username: string | null) => void;
  open: () => void;
  close: () => void;
  reset: () => void;
};

export const SleeperAuthContext =
  createContext<SleeperAuthContextType | null>(null);
