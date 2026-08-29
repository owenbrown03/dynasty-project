import { useMemo } from 'react';
import { ArrowLeft, ArrowRight, Check } from 'lucide-react';
import { formatMarketValue } from '@/utils/valueFormat';
import './TradeWinningBar.css';

export interface TradeWinningBarProps {
  teamAName?: string;
  teamBName?: string;
  teamANet: number;
  teamBNet: number;
  isMarketValue?: boolean;
}

export function TradeWinningBar({
  teamAName = 'Team 1',
  teamBName = 'Team 2',
  teamANet,
  teamBNet,
}: TradeWinningBarProps) {
  const { winner, diff, ratioA, ratioB } = useMemo(() => {
    const a = Math.max(0, teamANet);
    const b = Math.max(0, teamBNet);
    const total = a + b;
    const difference = Math.abs(a - b);

    if (total === 0) {
      return {
        winner: 'even' as const,
        diff: 0,
        ratioA: 50,
        ratioB: 50,
      };
    }

    const rawRatioA = (a / total) * 100;
    // Keep within bounds so neither side disappears completely
    const clampedA = Math.min(92, Math.max(8, rawRatioA));
    const clampedB = 100 - clampedA;

    // Consider even if within 2% or less than 50 points
    if (difference <= 50 || (total > 0 && Math.abs(rawRatioA - 50) < 2)) {
      return {
        winner: 'even' as const,
        diff: difference,
        ratioA: 50,
        ratioB: 50,
      };
    }

    if (a > b) {
      return {
        winner: 'team-a' as const,
        diff: difference,
        ratioA: clampedA,
        ratioB: clampedB,
      };
    }

    return {
      winner: 'team-b' as const,
      diff: difference,
      ratioA: clampedA,
      ratioB: clampedB,
    };
  }, [teamANet, teamBNet]);

  const hasAssets = teamANet > 0 || teamBNet > 0;

  return (
    <div className="trade-winning-bar-container">
      <div className="trade-meter-track" role="progressbar" aria-label="Trade balance meter">
        <div
          className={`trade-meter-fill trade-meter-fill-a ${winner === 'team-a' ? 'winning' : ''}`}
          style={{ width: `${ratioA}%` }}
        />
        <div className="trade-meter-center-notch" />
        <div
          className={`trade-meter-fill trade-meter-fill-b ${winner === 'team-b' ? 'winning' : ''}`}
          style={{ width: `${ratioB}%` }}
        />
      </div>

      <div className={`trade-result-banner ${winner}`}>
        {!hasAssets ? (
          <div className="trade-result-message">
            <span>Add players or picks to both sides to calculate trade balance</span>
          </div>
        ) : winner === 'even' ? (
          <div className="trade-result-message">
            <span className="trade-result-title">
              <Check size={16} className="trade-result-icon" /> Even Trade
            </span>
            <span className="trade-result-advice">
              Values are balanced within ~2%
            </span>
          </div>
        ) : winner === 'team-a' ? (
          <div className="trade-result-message">
            <span className="trade-result-title">
              <ArrowLeft size={16} className="trade-result-icon" /> Favors {teamAName}
            </span>
            <span className="trade-result-advice">
              Add a player or pick worth <strong>{formatMarketValue(diff)}</strong> to {teamBName} to even trade <ArrowRight size={13} style={{ display: 'inline', verticalAlign: 'middle' }} />
            </span>
          </div>
        ) : (
          <div className="trade-result-message">
            <span className="trade-result-title">
              Favors {teamBName} <ArrowRight size={16} className="trade-result-icon" />
            </span>
            <span className="trade-result-advice">
              <ArrowLeft size={13} style={{ display: 'inline', verticalAlign: 'middle' }} /> Add a player or pick worth <strong>{formatMarketValue(diff)}</strong> to {teamAName} to even trade
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
