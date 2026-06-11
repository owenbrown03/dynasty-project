import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react';

export type SleeperAuthStep = 'send' | 'verify';

type SleeperAuthContextType = {
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

const SleeperAuthContext =
  createContext<SleeperAuthContextType | null>(null);

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

export function useSleeperAuthContext() {
  const context = useContext(
    SleeperAuthContext,
  );

  if (!context) {
    throw new Error(
      'useSleeperAuthContext must be used within SleeperAuthProvider'
    );
  }

  return context;
}