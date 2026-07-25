import './Skeleton.css';

import type {
  CSSProperties,
} from 'react';

type SkeletonVariant =
  | 'block'
  | 'text'
  | 'title'
  | 'circle';

interface SkeletonProps {
  width?: number | string;
  height?: number | string;
  radius?: number | string;
  variant?: SkeletonVariant;
  className?: string;
}

function toCssValue(
  value: number | string | undefined,
) {
  if (typeof value === 'number') {
    return `${value}px`;
  }

  return value;
}

export function Skeleton({
  width,
  height,
  radius,
  variant = 'block',
  className = '',
}: SkeletonProps) {
  return (
    <span
      className={[
        'skeleton',
        variant === 'text' ? 'skeleton-text' : '',
        variant === 'title' ? 'skeleton-title' : '',
        variant === 'circle' ? 'skeleton-circle' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      style={{
        '--skeleton-width': toCssValue(width),
        '--skeleton-height': toCssValue(height),
        '--skeleton-radius': toCssValue(radius),
      } as CSSProperties}
      aria-hidden="true"
    />
  );
}
