import { useState } from 'react';
import { Link } from 'react-router';

import { useAdvisorRecommendations } from '@/hooks/sleeper/useAdvisor';
import { useAdvisorFeedback } from '@/hooks/sleeper/useAdvisorFeedback';
import { notify } from '@/utils/notify';
import type {
  AdvisorFeedbackTag,
  AdvisorPlayerRef,
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
      </span>
      <span className="advisor-chip-meta">
        {[
          player.position ?? '?',
          player.team ?? null,
          `KTC ${formatValue(player.ktc_value)}`,
        ]
          .filter(Boolean)
          .join(' · ')}
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
    lines.push(
      '',
      `**League:** ${proposal.league_name}`,
      `**Send:** ${proposal.send.map((p) => p.name).join(', ')}`,
      `**Receive:** ${proposal.receive.map((p) => p.name).join(', ')}`,
      `**KTC totals:** ${proposal.market_send_total ?? '?'} → ${proposal.market_receive_total ?? '?'}`,
    );
  }

  lines.push('', '_Auto-drafted from AI advisor feedback._');

  return lines.join('\n');
}

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
        <span className={`advisor-confidence ${confidenceClass}`}>
          {recommendation.confidence}
        </span>
      </header>

      <p className="advisor-pitch">“{recommendation.pitch}”</p>
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
          </div>
        </div>
      )}

      {proposal && (
        <footer className="advisor-totals">
          <span>
            KTC total:{' '}
            <strong>
              {formatValue(proposal.market_send_total)} →{' '}
              {formatValue(proposal.market_receive_total)}
            </strong>
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
      <section className="advisor-panel" aria-live="polite">
        <header className="advisor-panel-header">
          <p className="page-eyebrow">AI Advisor</p>
          <h3 className="trades-section-title">
            Generating recommendations...
          </h3>
        </header>
        <p className="page-description">
          Analyzing your roster, your valuations vs. the market, and
          leaguemate trade history in {leagueName}.
        </p>
      </section>
    );
  }

  if (cachedLoading && !recommendations) {
    return null;
  }

  if (!recommendations) {
    return (
      <section className="advisor-panel">
        <header className="advisor-panel-header">
          <p className="page-eyebrow">AI Advisor</p>
          <h3 className="trades-section-title">
            Trade recommendations for {leagueName}
          </h3>
        </header>
        <p className="page-description">
          The AI advisor cross-references your roster, your personal
          valuations vs. market prices, and how your leaguemates in this
          league actually trade — then proposes specific offers with a
          pitch you can send.
        </p>

        {errorMessage && (
          <div className="advisor-error-banner" role="alert">
            {errorMessage}
          </div>
        )}

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
        <p className="page-eyebrow">AI Advisor</p>
        <h3 className="trades-section-title">
          Your recommendations
        </h3>
        {recommendations.cached && (
          <span className="advisor-cached-badge">cached</span>
        )}
      </header>

      {recommendations.summary && (
        <p className="page-description">{recommendations.summary}</p>
      )}

      {errorMessage && (
        <div className="advisor-error-banner" role="alert">
          {errorMessage}
        </div>
      )}

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
