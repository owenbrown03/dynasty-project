import { useState } from 'react';
import { Link } from 'react-router';

import {
  useAdvisorDirectives,
  useAdvisorRecommendations,
  useInvalidateAdvisorRecommendations,
} from '@/hooks/sleeper/useAdvisor';
import {
  useAdvisorFeedback,
  useAdvisorLeagueFeedback,
} from '@/hooks/sleeper/useAdvisorFeedback';
import { useSendAdvisorOffer } from '@/hooks/sleeper/useSendAdvisorOffer';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { Skeleton } from '@/components/feedback/Skeleton';
import { notify } from '@/utils/notify';
import type {
  AdvisorFeedbackTag,
  AdvisorPickRef,
  AdvisorDirective,
  AdvisorPlayerRef,
  AdvisorProposal,
  AdvisorRecommendation,
} from '@/types';
import { ADVISOR_FEEDBACK_TAGS } from '@/types';

import { useLeagueDetails, useSaveUserNote } from '@/hooks/sleeper/useLeagues';
import './AdvisorPanel.css';

const TAG_LABELS: Record<AdvisorFeedbackTag, string> = {
  avoid_injured: 'Avoid injured players',
  roster_limit_concern: 'Roster limit concern',
  calculator_not_bible: 'Calculator isn\'t the bible',
  prefer_picks: 'Prefer draft picks',
  avoid_player: 'Avoid this player',
  position_need: 'Not a position need',
  age_window: 'Age window mismatch',
};

const CONFIDENCE_CLASS_BY_LABEL: Record<string, string> = {
  high: 'advisor-confidence-high',
  medium: 'advisor-confidence-medium',
  low: 'advisor-confidence-low',
};

function formatValue(
  value: number | null | undefined,
  suffix = '',
) {
  if (value === null || value === undefined) return '—';
  return `${value.toLocaleString()}${suffix}`;
}

function formatGeneratedAt(iso: string): string {
  const then = new Date(iso).getTime();

  if (Number.isNaN(then)) return '';

  const minutes = Math.floor((Date.now() - then) / 60000);

  if (minutes < 1) return 'just now';
  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  }

  const days = Math.floor(hours / 24);
  if (days < 7) {
    return `${days} day${days === 1 ? '' : 's'} ago`;
  }

  return `on ${new Date(iso).toLocaleDateString()}`;
}

function PlayerChip({
  player,
  direction,
}: {
  player: AdvisorPlayerRef;
  direction: 'send' | 'receive';
}) {
  return (
    <div
      className={`advisor-player-chip advisor-chip-${direction}`}
    >
      <span className="advisor-chip-name">
        <span className="advisor-chip-name-text">{player.name}</span>
        {player.injury_status ? (
          <span className="advisor-injury-badge">
            {player.injury_status.toUpperCase()}
          </span>
        ) : null}
        {player.on_block ? (
          <span className="advisor-otb-badge">ON BLOCK</span>
        ) : null}
      </span>
      <span className="advisor-chip-meta">
        <span className="advisor-chip-fact">
          {player.position ?? '?'}
        </span>
        {player.team ? (
          <span className="advisor-chip-fact">{player.team}</span>
        ) : null}
        <span className="advisor-chip-fact">
          {`FC ${formatValue(player.market_value)}`}
        </span>
        {player.personal_war != null ? (
          <span className="advisor-chip-fact">
            {`${player.personal_war.toFixed(1)} W`}
          </span>
        ) : null}
      </span>
    </div>
  );
}

function PickChip({
  pick,
  direction,
}: {
  pick: AdvisorPickRef;
  direction: 'send' | 'receive';
}) {
  return (
    <div
      className={`advisor-player-chip advisor-pick-chip advisor-chip-${direction}`}
    >
      <span className="advisor-chip-name">
        <span className="advisor-chip-name-text">
          {pick.season} Rd {pick.round}
        </span>
        {pick.on_block ? (
          <span className="advisor-otb-badge">ON BLOCK</span>
        ) : null}
      </span>
      <span className="advisor-chip-meta">
        <span className="advisor-chip-fact">
          FC {formatValue(pick.market_value)}
        </span>
      </span>
    </div>
  );
}

type ProposalAsset =
  | {
      kind: 'player';
      player: AdvisorPlayerRef;
      direction: 'send' | 'receive';
    }
  | {
      kind: 'pick';
      pick: AdvisorPickRef;
      direction: 'send' | 'receive';
    }
  | {
      kind: 'waiver';
      direction: 'send' | 'receive';
      creditFc: number | null;
      creditWar: number | null;
    };

function WaiverCreditChip({
  direction,
  creditFc,
  creditWar,
}: {
  direction: 'send' | 'receive';
  creditFc: number | null;
  creditWar: number | null;
}) {
  return (
    <div
      className={`advisor-waiver-chip advisor-chip-${direction}`}
    >
      <span className="advisor-chip-name">
        Waiver refill
      </span>
      <span className="advisor-chip-meta">
        {creditFc ? (
          <span className="advisor-chip-fact">
            +{Math.round(creditFc)} FC
          </span>
        ) : null}
        {creditWar ? (
          <span className="advisor-chip-fact">
            +{creditWar.toFixed(2)} W
          </span>
        ) : null}
      </span>
    </div>
  );
}

function AssetCell({ asset }: { asset: ProposalAsset | null }) {
  if (!asset) {
    return <div className="advisor-asset-empty" />;
  }

  if (asset.kind === 'waiver') {
    return (
      <WaiverCreditChip
        direction={asset.direction}
        creditFc={asset.creditFc}
        creditWar={asset.creditWar}
      />
    );
  }

  if (asset.kind === 'pick') {
    return <PickChip pick={asset.pick} direction={asset.direction} />;
  }

  return (
    <PlayerChip player={asset.player} direction={asset.direction} />
  );
}

function buildProposalAssets(
  proposal: AdvisorProposal,
): { send: ProposalAsset[]; receive: ProposalAsset[] } {
  const send: ProposalAsset[] = [
    ...proposal.send.map(
      (player) =>
        ({
          kind: 'player',
          player,
          direction: 'send',
        } as ProposalAsset),
    ),
    ...(proposal.send_picks ?? []).map(
      (pick) =>
        ({
          kind: 'pick',
          pick,
          direction: 'send',
        } as ProposalAsset),
    ),
  ];

  const receive: ProposalAsset[] = [
    ...proposal.receive.map(
      (player) =>
        ({
          kind: 'player',
          player,
          direction: 'receive',
        } as ProposalAsset),
    ),
    ...(proposal.receive_picks ?? []).map(
      (pick) =>
        ({
          kind: 'pick',
          pick,
          direction: 'receive',
        } as ProposalAsset),
    ),
  ];

  const myFc = proposal.my_waiver_credit ?? null;
  const myWar = proposal.my_waiver_credit_war ?? null;
  const theirFc = proposal.their_waiver_credit ?? null;
  const theirWar = proposal.their_waiver_credit_war ?? null;

  if (myFc || myWar) {
    send.push({
      kind: 'waiver',
      direction: 'send',
      creditFc: myFc,
      creditWar: myWar,
    });
  }

  if (theirFc || theirWar) {
    receive.push({
      kind: 'waiver',
      direction: 'receive',
      creditFc: theirFc,
      creditWar: theirWar,
    });
  }

  return { send, receive };
}

function DeltaBadge({ delta }: { delta: number | null }) {
  if (delta === null || Number.isNaN(delta)) {
    return null;
  }

  const positive = delta >= 0;

  return (
    <span
      className={`advisor-delta-badge ${positive ? 'positive' : 'negative'}`}
    >
      {positive ? '+' : ''}
      {Math.round(delta * 100) / 100}
    </span>
  );
}

function ProposalMatrix({
  proposal,
}: {
  proposal: AdvisorProposal;
}) {
  const { send, receive } = buildProposalAssets(proposal);
  const rowCount = Math.max(send.length, receive.length);

  return (
    <div className="advisor-proposal-matrix">
      <div className="advisor-proposal-head">
        <span className="advisor-proposal-label">
          You send → {proposal.counterparty_name}
        </span>
        <span className="advisor-proposal-label">
          You receive ← ({proposal.league_name})
        </span>
      </div>

      {Array.from({ length: rowCount }).map((_, i) => (
        <div className="advisor-proposal-row" key={i}>
          <div>{send[i] ? <AssetCell asset={send[i]} /> : null}</div>
          <div>
            {receive[i] ? <AssetCell asset={receive[i]} /> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

function buildIssueText(
  recommendation: AdvisorRecommendation,
  reason: string,
  tags: string[],
): string {
  const { proposal } = recommendation;

  const lines = [
    '### AI advisor feedback',
    '',
    `**Headline:** ${recommendation.headline}`,
    `**Reason:** ${reason || '(none provided)'}`,
  ];

  if (tags.length) {
    lines.push(`**Tags:** ${tags.join(', ')}`);
  }

  if (proposal) {
    const pickBits = (picks?: AdvisorPickRef[]) =>
      (picks ?? [])
        .map((x) => `${x.season} Rd ${x.round}`)
        .join(', ');

    lines.push(
      '',
      `**League:** ${proposal.league_name}`,
      `**Send:** ${proposal.send.map((p) => p.name).join(', ')}`,
      `**Receive:** ${proposal.receive.map((p) => p.name).join(', ')}`,
      `**Market totals:** ${proposal.market_send_total ?? '?'} → ${proposal.market_receive_total ?? '?'}`,
    );

    if (proposal.send_picks?.length) {
      lines.push(`**Picks sent:** ${pickBits(proposal.send_picks)}`);
    }

    if (proposal.receive_picks?.length) {
      lines.push(
        `**Picks received:** ${pickBits(proposal.receive_picks)}`,
      );
    }
  }

  lines.push('', '_Auto-drafted from AI advisor feedback._');

  return lines.join('\n');
}

function AdvisorCardSkeleton() {
  return (
    <article className="advisor-card">
      <header className="advisor-card-header">
        <Skeleton width="70%" variant="title" />
        <Skeleton width={54} height={18} radius={999} />
      </header>
      <Skeleton width="100%" variant="text" />
      <Skeleton width="92%" variant="text" />
      <Skeleton width="96%" variant="text" />
      <div className="advisor-proposal-grid">
        <div className="advisor-proposal-side">
          <Skeleton width={90} variant="text" />
          <Skeleton width={140} height={34} radius={6} />
        </div>
        <div className="advisor-proposal-side">
          <Skeleton width={110} variant="text" />
          <Skeleton width={140} height={34} radius={6} />
        </div>
      </div>
    </article>
  );
}

function AdvisorPanelSkeleton({
  label,
}: {
  label: string;
}) {
  return (
    <section
      className="advisor-panel"
      role="status"
      aria-live="polite"
    >
      <span className="skeleton-sr-label">{label}</span>

      <header className="advisor-panel-header">
        <div>
          <Skeleton width={70} variant="text" />
          <Skeleton
            width={240}
            variant="title"
          />
        </div>
      </header>

      <Skeleton width="min(560px, 100%)" variant="text" />

      <div className="advisor-cards">
        <AdvisorCardSkeleton />
        <AdvisorCardSkeleton />
      </div>
    </section>
  );
}

function SendTradeSection({
  proposal,
}: {
  proposal: AdvisorProposal;
}) {
  const { canWrite } = useSleeperConnection();
  const { sendOffer, sending } = useSendAdvisorOffer();
  const [confirming, setConfirming] = useState(false);
  const [sent, setSent] = useState(false);

  if (sent) {
    return (
      <p className="advisor-sent-note">
        Offer sent to {proposal.counterparty_name} — manage
        it on Sleeper.
      </p>
    );
  }

  if (!canWrite) {
    return (
      <p className="advisor-send-hint">
        Verify your Sleeper account in settings to send
        offers directly from here.
      </p>
    );
  }

  if (
    proposal.your_roster_id == null
    || proposal.counterparty_roster_id == null
  ) {
    return (
      <p className="advisor-send-hint">
        Hit Regenerate to enable one-click sending for
        this recommendation.
      </p>
    );
  }

  if (!confirming) {
    return (
      <button
        type="button"
        className="button-secondary advisor-send-btn"
        onClick={() => setConfirming(true)}
      >
        Send this trade
      </button>
    );
  }

  return (
    <div
      className="advisor-send-confirm"
      role="alertdialog"
      aria-label="Confirm trade offer"
    >
      <div className="advisor-send-summary">
        <p className="advisor-send-copy">
          This sends a real offer on Sleeper and notifies the manager.
        </p>
        <div className="advisor-send-line">
          <span className="advisor-send-line-label">
            To
          </span>
          <span className="advisor-send-line-value">
            <strong>{proposal.counterparty_name}</strong>
            {proposal.counterparty_fringe ? (
              <span className="advisor-otb-badge">FRINGE</span>
            ) : proposal.counterparty_strategy ? (
              <span className="advisor-otb-badge">
                {proposal.counterparty_strategy === 'win_now'
                  ? 'CONTENDER'
                  : proposal.counterparty_strategy.toUpperCase()}
              </span>
            ) : null}
          </span>
        </div>
        <div className="advisor-send-line">
          <span className="advisor-send-line-label">
            You give
          </span>
          <span className="advisor-send-line-value">
            {proposal.send.map((p) => p.name).join(', ')}
            {proposal.send_picks?.length
              ? `, ${proposal.send_picks
                  .map((pk) => `${pk.season} Rd ${pk.round}`)
                  .join(', ')}`
              : ''}
          </span>
        </div>
        <div className="advisor-send-line">
          <span className="advisor-send-line-label">
            You receive
          </span>
          <span className="advisor-send-line-value">
            {proposal.receive.map((p) => p.name).join(', ')}
            {proposal.receive_picks?.length
              ? `, ${proposal.receive_picks
                  .map((pk) => `${pk.season} Rd ${pk.round}`)
                  .join(', ')}`
              : ''}
          </span>
        </div>
      </div>

      <div className="advisor-send-actions">
        <button
          type="button"
          className="button-secondary"
          disabled={sending}
          onClick={() => setConfirming(false)}
        >
          Cancel
        </button>
        <button
          type="button"
          className="button-primary"
          disabled={sending}
          onClick={() =>
            sendOffer(proposal, {
              onSuccess: () => setSent(true),
            })
          }
        >
          {sending ? 'Sending...' : 'Confirm & send'}
        </button>
      </div>
    </div>
  );
}

const STRATEGY_LABELS: Record<string, string> = {
  rebuild: 'Rebuild',
  win_now: 'Win now',
  hoard_picks: 'Hoard picks',
  compete: 'Compete',
};

function RecommendationCard({
  recommendation,
}: {
  recommendation: AdvisorRecommendation;
}) {
  const { proposal } = recommendation;
  const { save, saving } = useAdvisorFeedback();

  const [vote, setVote] = useState<'like' | 'dislike' | null>(null);
  const [reason, setReason] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [submitted, setSubmitted] = useState(false);

  const confidenceClass =
    CONFIDENCE_CLASS_BY_LABEL[recommendation.confidence] ??
    'advisor-confidence-medium';

  const involvedPlayers: AdvisorPlayerRef[] = proposal
    ? [...proposal.send, ...proposal.receive]
    : [];

  async function submitFeedback(sentiment: 'like' | 'dislike') {
    try {
      await save({
        sentiment,
        reason: reason || null,
        tags: selectedTags,
        league_id: proposal?.league_id ?? null,
        counterparty_id: proposal?.counterparty_id ?? null,
        player_ids: involvedPlayers.map((p) => p.player_id),
        proposal_snapshot: proposal
          ? (proposal as unknown as Record<string, unknown>)
          : {},
      });
      setSubmitted(true);
    } catch {
      // notify handled in hook
    }
  }

  function copyIssue() {
    const text = buildIssueText(recommendation, reason, selectedTags);

    navigator.clipboard.writeText(text).then(
      () => notify.success('GitHub issue draft copied to clipboard.'),
      () => notify.error('Could not copy to clipboard.'),
    );
  }

  function toggleTag(tag: string) {
    setSelectedTags((current) =>
      current.includes(tag)
        ? current.filter((t) => t !== tag)
        : [...current, tag],
    );
  }

  return (
    <article className="advisor-card">
      <header className="advisor-card-header">
        <h4 className="advisor-headline">
          {recommendation.headline}
        </h4>
        <span className="advisor-header-badges">
          {proposal?.strategy
            ? (
                STRATEGY_LABELS[proposal.strategy]
                ?? proposal.strategy
              ) && (
                <span className={`advisor-strategy-badge advisor-strategy-${proposal.strategy}`}>
                  {STRATEGY_LABELS[proposal.strategy]
                    ?? proposal.strategy}
                </span>
              )
            : null}
          <span className={`advisor-confidence ${confidenceClass}`}>
            {recommendation.confidence}
          </span>
        </span>
      </header>

      <p className="advisor-reasoning">{recommendation.reasoning}</p>

      {proposal && <ProposalMatrix proposal={proposal} />}

      {proposal && (() => {
        const marketSendAdj =
          (proposal.market_send_total ?? 0)
          + (proposal.my_waiver_credit ?? 0);
        const marketRecvAdj =
          (proposal.market_receive_total ?? 0)
          + (proposal.their_waiver_credit ?? 0);
        const warSend =
          proposal.personal_send_total ?? 0;
        const warRecvAdj =
          (proposal.personal_receive_total ?? 0)
          + (proposal.my_waiver_credit_war ?? 0);

        return (
          <footer className="advisor-totals">
            <div className="advisor-total-block">
              <span className="advisor-total-label">Market</span>
              <span className="advisor-total-value">
                {formatValue(marketSendAdj)}
                {' \u2192 '}
                {formatValue(marketRecvAdj)}
                <DeltaBadge delta={marketRecvAdj - marketSendAdj} />
              </span>
            </div>
            <div className="advisor-total-block">
              <span className="advisor-total-label">Mine</span>
              <span className="advisor-total-value">
                {formatValue(warSend, ' W')}
                {' \u2192 '}
                {formatValue(warRecvAdj, ' W')}
                <DeltaBadge delta={warRecvAdj - warSend} />
              </span>
            </div>
          </footer>
        );
      })()}

      {proposal && <SendTradeSection proposal={proposal} />}

      <footer className="advisor-feedback-row">
        {submitted ? (
          <span className="advisor-feedback-thanks">
            Thanks — noted for future recommendations.
          </span>
        ) : vote === null ? (
          <>
            <button
              type="button"
              className="button-secondary advisor-feedback-btn"
              disabled={saving}
              onClick={() => {
                setVote('like');
                void submitFeedback('like');
              }}
            >
              Good rec
            </button>
            <button
              type="button"
              className="button-secondary advisor-feedback-btn"
              disabled={saving}
              onClick={() => setVote('dislike')}
            >
              Not for me
            </button>
          </>
        ) : (
          <div className="advisor-feedback-form">
            <textarea
              className="advisor-feedback-reason"
              placeholder="Why not? (e.g. I'd exceed the roster limit, this is best ball and he's injured, calculator isn't the bible...)"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              rows={2}
            />

            <div className="advisor-tag-row">
              {ADVISOR_FEEDBACK_TAGS.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  className={`advisor-tag-chip ${
                    selectedTags.includes(tag) ? 'advisor-tag-active' : ''
                  }`}
                  onClick={() => toggleTag(tag)}
                >
                  {TAG_LABELS[tag]}
                </button>
              ))}
            </div>

            <div className="advisor-feedback-actions">
              <button
                type="button"
                className="button-secondary"
                disabled={saving}
                onClick={() => void submitFeedback('dislike')}
              >
                Save feedback
              </button>

              {involvedPlayers.length === 1 && (
                <Link
                  to="/my-values"
                  className="button-secondary"
                  onClick={() => {
                    void submitFeedback('dislike');
                  }}
                >
                  Downgrade {involvedPlayers[0].name} in My Values
                </Link>
              )}

              <button
                type="button"
                className="button-secondary"
                onClick={copyIssue}
              >
                Copy as GitHub issue
              </button>
            </div>
          </div>
        )}
      </footer>
    </article>
  );
}


function DirectiveDropChip({
  player,
}: {
  player: AdvisorPlayerRef;
}) {
  return (
    <div className="advisor-player-chip advisor-chip-send">
      <span className="advisor-chip-name">
        <span className="advisor-chip-name-text">{player.name}</span>
        {player.injury_status ? (
          <span className="advisor-injury-badge">
            {player.injury_status.toUpperCase()}
          </span>
        ) : null}
      </span>
      <span className="advisor-chip-meta">
        <span className="advisor-chip-fact">
          {player.position ?? '?'}
        </span>
        {player.team ? (
          <span className="advisor-chip-fact">{player.team}</span>
        ) : null}
        <span className="advisor-chip-fact">
          {`FC ${formatValue(player.market_value)}`}
        </span>
      </span>
    </div>
  );
}

function AdvisorDirectives({ leagueId }: { leagueId: string }) {
  const { directives, loading } = useAdvisorDirectives({ leagueId });

  if (loading || directives.length === 0) {
    return null;
  }

  return (
    <div className="advisor-directives" role="alert">
      {directives.map((directive: AdvisorDirective) => (
        <div
          key={directive.league_id}
          className="advisor-directive-card"
        >
          <p className="advisor-directive-title">
            {directive.league_name} is{' '}
            <strong>
              {directive.over_limit_by} player
              {directive.over_limit_by === 1 ? '' : 's'}
            </strong>{' '}
            over its roster limit
            {directive.status === 'pre_draft'
              ? ' — fix this before your draft starts'
              : ''}
          </p>
          {directive.suggested_drops.length > 0 && (
            <div className="advisor-directive-drops">
              <span className="advisor-directive-label">
                Suggested drops:
              </span>
              {directive.suggested_drops.map((drop) => (
                <DirectiveDropChip
                  key={drop.player_id}
                  player={drop}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}


function AdvisorContextPanel({
  leagueId,
  username,
}: {
  leagueId: string;
  username: string;
}) {
  const feedbackList = useAdvisorLeagueFeedback(leagueId);
  const invalidate = useInvalidateAdvisorRecommendations();
  const noteState = useLeagueDetails(leagueId, true);
  const saveNote = useSaveUserNote();
  const [noteDraft, setNoteDraft] = useState<string | null>(null);

  const savedNote = noteState.data?.note ?? '';
  const noteValue = noteDraft ?? savedNote;
  const noteDirty = noteDraft !== null && noteDraft !== savedNote;

  const handleSaveNote = async () => {
    try {
      await saveNote.saveNote({
        league_id: leagueId,
        note: noteValue,
      });
      setNoteDraft(null);
      notify.success('AI context note saved.');
    } catch {
      notify.error('Could not save the note.');
    }
  };

  const handleRemoveEntry = async (id: number) => {
    try {
      await feedbackList.remove(id);
      notify.success('Feedback entry removed.');
    } catch {
      notify.error('Could not remove feedback entry.');
    }
  };

  const handleInvalidate = async () => {
    try {
      await invalidate.invalidate({ username, leagueId });
      notify.success(
        'Cached recommendations cleared — hit Generate for a fresh take.',
      );
    } catch {
      notify.error('Could not clear cached recommendations.');
    }
  };

  return (
    <section className="advisor-context-panel">
      <header className="advisor-panel-header">
        <p className="page-eyebrow">AI context</p>
        <h4 className="advisor-subheading">
          What the advisor knows about you here
        </h4>
      </header>

      <label className="advisor-context-note">
        <span className="advisor-directive-label">
          Direction note (treated as standing instructions)
        </span>
        <textarea
          value={noteValue}
          rows={2}
          placeholder="e.g. Selling everything, full rebuild for 2027 picks."
          onChange={(event) => setNoteDraft(event.target.value)}
        />
        {noteDirty && (
          <button
            type="button"
            className="button-secondary advisor-context-save"
            disabled={saveNote.saving}
            onClick={() => {
              void handleSaveNote();
            }}
          >
            {saveNote.saving ? 'Saving…' : 'Save note'}
          </button>
        )}
      </label>

      <div className="advisor-context-feedback">
        <span className="advisor-directive-label">
          {feedbackList.entries.length === 0
            ? 'No feedback remembered for this league yet'
            : `${feedbackList.entries.length} feedback ${feedbackList.entries.length === 1 ? 'entry' : 'entries'} remembered for this league`}
        </span>
        {feedbackList.entries.map((entry) => (
          <div
            key={entry.id}
            className="advisor-context-entry"
          >
            <span
              className={`advisor-context-entry-sentiment ${entry.sentiment}`}
            >
              {entry.sentiment}
            </span>
            <span className="advisor-context-entry-text">
              {entry.reason || entry.tags.join(', ') || '(no detail)'}
            </span>
            <button
              type="button"
              className="my-values-rank-reset"
              title="Delete this feedback entry"
              disabled={feedbackList.removing}
              onClick={() => {
                void handleRemoveEntry(entry.id);
              }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <button
        type="button"
        className="button-secondary advisor-context-invalidate"
        disabled={invalidate.saving}
        onClick={() => {
          void handleInvalidate();
        }}
      >
        {invalidate.saving ? 'Clearing…' : 'Invalidate cached recommendations'}
      </button>
    </section>
  );
}

interface AdvisorPanelProps {
  leagueId: string;
  leagueName: string;
}

export const AdvisorPanel = ({
  leagueId,
  leagueName,
}: AdvisorPanelProps) => {
  const {
    username,
    recommendations,
    cachedLoading,
    loading,
    errorMessage,
    generate,
    reset,
  } = useAdvisorRecommendations({ leagueId });
  const [dismissed, setDismissed] = useState(false);

  if (!username || dismissed) {
    return null;
  }

  if (loading) {
    return (
      <AdvisorPanelSkeleton label="Generating recommendations..." />
    );
  }

  if (cachedLoading && !recommendations) {
    return (
      <AdvisorPanelSkeleton
        label="Checking for saved recommendations..."
      />
    );
  }

  if (!recommendations) {
    return (
      <section className="advisor-panel">
        <header className="advisor-panel-header">
          <p className="page-eyebrow">Roster Lab</p>
          <h3 className="trades-section-title">
            Trade recommendations for {leagueName}
          </h3>
        </header>
        <p className="page-description">
          The AI advisor cross-references your roster, your personal
          valuations vs. market prices, and how your leaguemates in this
          league actually trade — then proposes specific offers with the
          reasoning behind each one.
        </p>

        {errorMessage && (
          <div className="advisor-error-banner" role="alert">
            {errorMessage}
          </div>
        )}

        <AdvisorDirectives leagueId={leagueId} />

        <AdvisorContextPanel
          leagueId={leagueId}
          username={username}
        />

        <button
          type="button"
          className="button-secondary"
          disabled={loading}
          onClick={() => generate()}
        >
          Generate AI trade recommendations for this league
        </button>
      </section>
    );
  }

  const hasContent =
    recommendations.recommendations.length > 0 ||
    recommendations.roster_advice.length > 0;

  return (
    <section className="advisor-panel">
      <header className="advisor-panel-header">
        <p className="page-eyebrow">Roster Lab</p>
        <h3 className="trades-section-title">
          Your recommendations
        </h3>
        {recommendations.cached && (
          <span className="advisor-cached-badge">cached</span>
        )}
      </header>

      {recommendations.generated_at && (
        <p className="advisor-generated-at">
          Generated{' '}
          {formatGeneratedAt(recommendations.generated_at)}
          {recommendations.cached
            ? ' — hit Regenerate for a fresh take'
            : ''}
        </p>
      )}

      {recommendations.summary && (
        <p className="page-description">{recommendations.summary}</p>
      )}

      {errorMessage && (
        <div className="advisor-error-banner" role="alert">
          {errorMessage}
        </div>
      )}

      <AdvisorDirectives leagueId={leagueId} />

      {hasContent ? (
        <>
          <div className="advisor-cards">
            {recommendations.recommendations.map((rec, index) => (
              <RecommendationCard
                key={`trade-${index}`}
                recommendation={rec}
              />
            ))}
          </div>

          {recommendations.roster_advice.length > 0 && (
            <>
              <h4 className="advisor-subheading">
                Roster construction notes
              </h4>
              <div className="advisor-cards">
                {recommendations.roster_advice.map((rec, index) => (
                  <RecommendationCard
                    key={`roster-${index}`}
                    recommendation={rec}
                  />
                ))}
              </div>
            </>
          )}
        </>
      ) : (
        <p className="no-results-text">
          The advisor didn't find enough data in this league for concrete
          recommendations yet — keep the league synced and check back.
        </p>
      )}

      <footer className="advisor-panel-footer">
        <button
          type="button"
          className="button-secondary"
          onClick={() => {
            reset();
            setDismissed(true);
          }}
        >
          Dismiss
        </button>
        <button
          type="button"
          className="button-secondary"
          disabled={loading}
          onClick={() => generate()}
        >
          Regenerate
        </button>
      </footer>
    </section>
  );
};
