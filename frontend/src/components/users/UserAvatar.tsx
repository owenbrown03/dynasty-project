import { useMemo, useState } from 'react';

import { getPlayerInitials } from '@/utils/players';

interface UserAvatarProps {
  avatarId?: string | null;
  name: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

function getSleeperUserAvatarUrl(
  avatarId: string | null | undefined,
): string | null {
  if (!avatarId) {
    return null;
  }

  return `https://sleepercdn.com/avatars/thumbs/${avatarId}`;
}

export function UserAvatar({
  avatarId,
  name,
  size = 'md',
  className = '',
}: UserAvatarProps) {
  const [hasError, setHasError] = useState(false);

  const imageUrl = useMemo(
    () => getSleeperUserAvatarUrl(avatarId),
    [avatarId],
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
      alt={`${name} avatar`}
      loading="lazy"
      onError={() => {
        setHasError(true);
      }}
    />
  );
}
