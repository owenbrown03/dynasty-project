import { useMemo, useState } from 'react';

import {
  getPlayerInitials,
  getSleeperPlayerHeadshotUrl,
} from '@/utils/players';


interface PlayerAvatarProps {
  playerId?: string | null;
  name: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}


export function PlayerAvatar({
  playerId,
  name,
  size = 'md',
  className = '',
}: PlayerAvatarProps) {
  const [hasError, setHasError] = useState(false);

  const imageUrl = useMemo(
    () => getSleeperPlayerHeadshotUrl(playerId),
    [playerId],
  );

  const avatarClassName = [
    'player-avatar',
    `player-avatar-${size}`,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  if (!imageUrl || hasError) {
    return (
      <span
        className={`${avatarClassName} player-avatar-fallback`}
        aria-hidden="true"
      >
        {getPlayerInitials(name)}
      </span>
    );
  }

  return (
    <img
      className={avatarClassName}
      src={imageUrl}
      alt={`${name} headshot`}
      loading="lazy"
      onError={() => {
        setHasError(true);
      }}
    />
  );
}
