import { createContext, useCallback, useState } from 'react';

export interface MobileNavState {
  open: boolean;
  toggle: () => void;
  close: () => void;
}

export const MobileNavContext = createContext<MobileNavState>({
  open: false,
  toggle: () => {},
  close: () => {},
});

export function MobileNavProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const toggle = useCallback(() => setOpen((prev) => !prev), []);
  const close = useCallback(() => setOpen(false), []);

  return (
    <MobileNavContext.Provider value={{ open, toggle, close }}>
      {children}
    </MobileNavContext.Provider>
  );
}
