import { useState } from 'react';
import { Link } from 'react-router';

import {
  useAdvisorDirectives,
  useAdvisorRecommendations,
} from '@/hooks/sleeper/useAdvisor';
import { useAdvisorFeedback } from '@/hooks/sleeper/useAdvisorFeedback';
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
        {player.name}
        {player.on_block ? (
          <span className="advisor-otb-badge">ON BLOCK</span>
        ) : null}
      </span>
      <span className="advisor-chip-meta">
        {[
          player.position ?? '?',
          player.team ?? null,
          `FC ${formatValue(player.market_value)}`,
        ]
          .filter(Boolean)
          .join(' · ')}
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
        {pick.season} Rd {pick.round}
        {pick.on_block ? (
          <span className="advisor-otb-badge">ON BLOCK</span>
        ) : null}
      </span>
      <span className="advisor-chip-meta">
        FC {formatValue(pick.market_value)}
      </span>
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
      <p>
        This sends a real offer on Sleeper to{' '}
        <strong>{proposal.counterparty_name}</strong>:{' '}
        you give{' '}
        {proposal.send.map((p) => p.name).join(', ')} and
        receive{' '}
        {proposal.receive.map((p) => p.name).join(', ')}.
      </p>

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

      {proposal && (
        <div className="advisor-proposal-grid">
          <div className="advisor-proposal-side">
            <span className="advisor-proposal-label">
              You send → {proposal.counterparty_name}
            </span>

            {proposal.send.map((player) => (
              <PlayerChip
                key={`send-${player.player_id}`}
                player={player}
                direction="send"
              />
            ))}

            {(proposal.send_picks ?? []).map((pick) => (
              <PickChip
                key={`send-pick-${pick.season}-${pick.round}-${pick.og_roster_id}`}
                pick={pick}
                direction="send"
              />
            ))}
          </div>

          <div className="advisor-proposal-side">
            <span className="advisor-proposal-label">
              You receive ← ({proposal.league_name})
            </span>

            {proposal.receive.map((player) => (
              <PlayerChip
                key={`receive-${player.player_id}`}
                player={player}
                direction="receive"
              />
            ))}

            {(proposal.receive_picks ?? []).map((pick) => (
              <PickChip
                key={`receive-pick-${pick.season}-${pick.round}-${pick.og_roster_id}`}
                pick={pick}
                direction="receive"
              />
            ))}
          </div>
        </div>
      )}

      {proposal && (
        <footer className="advisor-totals">
          <span>
            Market (FC) total:{' '}
            <strong>
              {formatValue(
                (proposal.my_waiver_credit
                  ? (proposal.market_send_total ?? 0)
                    + proposal.my_waiver_credit
                  : proposal.market_send_total),
              )} →{' '}
              {formatValue(
                (proposal.their_waiver_credit
                  ? (proposal.market_receive_total ?? 0)
                    + proposal.their_waiver_credit
                  : proposal.market_receive_total),
              )}
            </strong>
            {proposal.their_waiver_credit ? (
              <span className="advisor-waiver-inline">
                {' '}incl. +{Math.round(proposal.their_waiver_credit)}{' '}
                waiver to them
              </span>
            ) : null}
            {proposal.my_waiver_credit ? (
              <span className="advisor-waiver-inline">
                {' '}incl. +{Math.round(proposal.my_waiver_credit)}{' '}
                waiver to you
              </span>
            ) : null}
          </span>
          <span>
            Your WAR total:{' '}
            <strong>
              {formatValue(proposal.personal_send_total, ' W')} →{' '}
              {formatValue(proposal.personal_receive_total, ' W')}
            </strong>
          </span>
        </footer>
      )}

      {proposal
        && (proposal.my_waiver_credit
          || proposal.their_waiver_credit) && (
        <p className="advisor-waiver-note">
          Incl. waiver-spot credit{' '}
          {proposal.my_waiver_credit
            ? `to you (+${Math.round(proposal.my_waiver_credit)})`
            : `to ${proposal.counterparty_name} (+${Math.round(
                proposal.their_waiver_credit ?? 0,
              )})`}
          {' '}for the uneven asset count.
        </p>
      )}

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
      <span className="advisor-chip-name">{player.name}</span>
      <span className="advisor-chip-meta">
        {[
          player.position ?? '?',
          player.team ?? null,
          `FC ${formatValue(player.market_value)}`,
        ]
          .filter(Boolean)
          .join(' \u00b7 ')}
      </span>
    </div>
  );
}

function AdvisorDirectives() {
  const { directives, loading } = useAdvisorDirectives();

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

        <AdvisorDirectives />

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

      <AdvisorDirectives />

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
