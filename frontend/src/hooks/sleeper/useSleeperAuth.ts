import { useSleeperAuthFlow } from './useSleeperAuthFlow';
import { useSleeperAuthUI } from './useSleeperAuthUI';

export const useSleeperAuth = () => {
  const flow = useSleeperAuthFlow();
  const ui = useSleeperAuthUI();

  return {
    ...flow,
    ...ui,
  };
};