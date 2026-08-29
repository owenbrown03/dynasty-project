import { useState } from 'react';
import { getSleeperTeamLogoUrl } from '@/utils/players';
import './TeamBadge.css';

export interface TeamBadgeProps {
  team?: string | null;
  size?: 'xs' | 'sm' | 'md';
  showLabel?: boolean;
  className?: string;
  fallbackText?: string;
}

export function TeamBadge({
  team,
  size = 'sm',
  showLabel = true,
  className = '',
  fallbackText = 'FA',
}: TeamBadgeProps) {
  const [hasError, setHasError] = useState(false);
  const logoUrl = !hasError ? getSleeperTeamLogoUrl(team) : null;
  const displayTeam = team?.trim() || fallbackText;

  return (
    <span className={`team-badge team-badge-${size} ${className}`.trim()}>
      {logoUrl ? (
        <img
          src={logoUrl}
          alt={`${displayTeam} logo`}
          className="team-badge-logo"
          loading="lazy"
          onError={() => setHasError(true)}
        />
      ) : null}
      {showLabel ? <span className="team-badge-label">{displayTeam}</span> : null}
    </span>
  );
}
