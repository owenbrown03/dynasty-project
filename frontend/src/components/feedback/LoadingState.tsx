import { LoaderCircle } from 'lucide-react';

interface LoadingStateProps {
  label: string;
  inline?: boolean;
  className?: string;
}

export function LoadingState({
  label,
  inline = false,
  className = '',
}: LoadingStateProps) {
  return (
    <div
      className={[
        inline
          ? 'loading-state loading-state-inline'
          : 'loading-state',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      role="status"
      aria-live="polite"
    >
      <LoaderCircle
        className="site-spinner"
        size={18}
        aria-hidden="true"
      />

      <span>{label}</span>
    </div>
  );
}
