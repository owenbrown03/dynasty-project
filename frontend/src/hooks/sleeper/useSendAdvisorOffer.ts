import { useMutation } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import type {
  AdvisorPickRef,
  AdvisorProposal,
  BulkTradeProposalRequest,
} from '@/types';
import { extractErrorDetail } from './useAdvisor';

function buildOfferPayload(
  proposal: AdvisorProposal,
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
      },
    ],
  };
}

export function useSendAdvisorOffer() {
  const mutation = useMutation({
    mutationFn: async (proposal: AdvisorProposal) => {
      const response = await api.trades.submitBulkOffers(
        buildOfferPayload(proposal),
      );

      return response.data.results[0] ?? null;
    },
    onSuccess: (result) => {
      if (result?.success) {
        notify.success('Trade offer sent on Sleeper.');
      } else {
        notify.error(
          result?.error
            ?? 'Sleeper rejected this offer.',
        );
      }
    },
    onError: (error) => {
      notify.error(
        extractErrorDetail(error)
          ?? 'Could not send this offer. Try again shortly.',
      );
    },
  });

  return {
    sendOffer: mutation.mutate,
    sending: mutation.isPending,
  };
}
