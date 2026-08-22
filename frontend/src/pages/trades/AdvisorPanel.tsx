import { useState } from 'react';

import { useAdvisorRecommendations } from '@/hooks/sleeper/useAdvisor';
import type {
  AdvisorPlayerRef,
  AdvisorRecommendation,
} from '@/types';

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

function RecommendationCard({
  recommendation,
}: {
  recommendation: AdvisorRecommendation;
}) {
  const { proposal } = recommendation;

  const confidenceClass =
    CONFIDENCE_CLASS_BY_LABEL[recommendation.confidence] ??
    'advisor-confidence-medium';

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
    </article>
  );
}

export const AdvisorPanel = () => {
  const {
    username,
    recommendations,
    loading,
    generate,
    reset,
  } = useAdvisorRecommendations();
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
          Analyzing your rosters, your valuations vs. the market, and leaguemate trade history across your leagues.
        </p>
      </section>
    );
  }

  if (!recommendations) {
    return (
      <section className="advisor-panel">
        <header className="advisor-panel-header">
          <p className="page-eyebrow">AI Advisor</p>
          <h3 className="trades-section-title">
            Trade recommendations for you
          </h3>
        </header>
        <p className="page-description">
          The AI advisor cross-references your rosters, your personal valuations vs. market prices, and how your leaguemates actually trade — then proposes specific offers with a pitch you can send.
        </p>
        <button
          type="button"
          className="button-secondary"
          onClick={() => generate()}
        >
          Generate AI trade recommendations
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
          The advisor didn't find enough data for concrete recommendations yet — keep your leagues synced and check back.
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
          onClick={() => generate()}
        >
          Regenerate
        </button>
      </footer>
    </section>
  );
};
