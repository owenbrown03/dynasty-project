import { UserAvatar } from '@/components/users/UserAvatar';

interface LeagueAvatarProps {
  avatarId?: string | null;
  name: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/**
 * League avatars use the same Sleeper CDN path as user avatars:
 * https://sleepercdn.com/avatars/thumbs/{avatarId}
 */
export function LeagueAvatar({
  avatarId,
  name,
  size = 'md',
  className = '',
}: LeagueAvatarProps) {
  return (
    <UserAvatar
      avatarId={avatarId}
      name={name}
      size={size}
      className={className}
    />
  );
}
