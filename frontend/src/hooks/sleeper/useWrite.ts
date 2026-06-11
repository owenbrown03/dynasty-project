import { useMutation, useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import type { TradeRequest, WaiverRequest } from '@/types';

const TRADE_KEY = ['trades'] as const;
const WAIVER_KEY = ['waivers'] as const;

export function useWrite() {
  const queryClient = useQueryClient();


  const proposeTradeMutation = useMutation({
    mutationFn: (payload: TradeRequest) =>
      api.write.proposeTrade(payload),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRADE_KEY });
    },
  });

  const waiverMutation = useMutation({
    mutationFn: (payload: WaiverRequest) =>
      api.write.submitWaiverClaim(payload),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WAIVER_KEY });
    },
  });


  return {
    proposeTrade: proposeTradeMutation.mutateAsync,
    submitWaiverClaim: waiverMutation.mutateAsync,

    isProposingTrade: proposeTradeMutation.isPending,
    isSubmittingWaiver: waiverMutation.isPending,

    proposeTradeMutation,
    waiverMutation,
  };
}