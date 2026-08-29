import { useMutation } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type {
  AdvisorPickRef,
  AdvisorProposal,
  BulkTradeProposalRequest,
  BulkTradeProposalResult,
} from '@/types';
import { extractErrorDetail } from './useAdvisor';

export interface AdvisorOfferOptions {
  expiresAt?: number | null;
  sendDm?: boolean;
  onSuccess?: (result: BulkTradeProposalResult | null) => void;
}

function buildOfferPayload(
  proposal: AdvisorProposal,
  options?: AdvisorOfferOptions,
): BulkTradeProposalRequest {
  const toPickRefs = (picks: AdvisorPickRef[] = []) =>
    picks.map((pick) => ({
      season: pick.season,
      round: pick.round,
      og_roster_id: pick.og_roster_id,
    }));

  return {
    offers: [
      {
        league_id: proposal.league_id,
        your_roster_id: proposal.your_roster_id!,
        counterparty_roster_id:
          proposal.counterparty_roster_id!,
        send_player_ids: proposal.send.map(
          (player) => player.player_id,
        ),
        send_picks: toPickRefs(proposal.send_picks),
        receive_player_ids: proposal.receive.map(
          (player) => player.player_id,
        ),
        receive_picks: toPickRefs(
          proposal.receive_picks,
        ),
        expires_at: options?.expiresAt ?? null,
        send_dm: options?.sendDm ?? false,
      },
    ],
  };
}

export function useSendAdvisorOffer() {
  const mutation = useMutation({
    mutationFn: async (variables: {
      proposal: AdvisorProposal;
      options?: AdvisorOfferOptions;
    }) => {
      const { proposal, options } = variables;
      const response = await api.trades.submitBulkOffers(
        buildOfferPayload(proposal, options),
      );

      return response.data.results[0] ?? null;
    },
    onSuccess: (result, variables) => {
      if (result?.success) {
        notify.success('Trade offer sent on Sleeper.');
      } else {
        notify.error(
          result?.error
            ?? 'Sleeper rejected this offer.',
        );
      }
      variables.options?.onSuccess?.(result);
    },
    onError: (error) => {
      notify.error(
        extractErrorDetail(error)
          ?? 'Could not send this offer. Try again shortly.',
      );
    },
  });

  return {
    sendOffer: (
      proposal: AdvisorProposal,
      options?: AdvisorOfferOptions,
    ) => mutation.mutate({ proposal, options }),
    sending: mutation.isPending,
  };
}
