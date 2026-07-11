import {
  useState,
  type ReactNode,
} from 'react';

import {
  SleeperAuthContext,
  type SleeperAuthStep,
} from '@/context/sleeper-auth-context';

export function SleeperAuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [isOpen, setOpen] = useState(false);
  
  const [step, setStep] =
    useState<SleeperAuthStep>('send');

  const [username, setUsername] =
    useState<string | null>(null);

  const [captcha, setCaptcha] = 
    useState<string | null>(null);

  const open = () => {
    setOpen(true);
  };

  const close = () => {
    setOpen(false);
    reset();
  };

  const reset = () => {
    setStep('send');
    setUsername(null);
    setCaptcha(null);
  };

  return (
    <SleeperAuthContext.Provider
      value={{
        isOpen,
        step,
        username,
        captcha,

        setStep,
        setUsername,
        setCaptcha,

        open,
        close,
        reset,
      }}
    >
      {children}
    </SleeperAuthContext.Provider>
  );
}
