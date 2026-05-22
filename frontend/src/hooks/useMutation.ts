import { useApi } from '@/context/ApiContext';

export function useMutation<T, P = void>(
  key: string, 
  mutationFn: (payload: P) => Promise<T>
) {
  const { isCalling, executeCall } = useApi();

  const mutate = async (payload?: P) => {
    return await executeCall(key, () => mutationFn(payload as P));
  };

  const mutateAsync = async (payload?: P) => {
    return await executeCall(key, () => mutationFn(payload as P));
  };

  return { 
    mutate, 
    mutateAsync,
    loading: isCalling(key) 
  };
}