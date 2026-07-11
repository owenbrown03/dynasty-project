import { BootstrapContext } from '@/context/bootstrap-context';
import { useBootstrap } from '@/hooks/useBootstrap';

export function BootstrapProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const query = useBootstrap();

  return (
    <BootstrapContext.Provider
      value={{
        bootstrap: query.data,
        isLoading: query.isLoading,
      }}
    >
      {children}
    </BootstrapContext.Provider>
  );
}
