import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { useBootstrap } from '@/hooks/useBootstrap';
import type { Bootstrap, ThemePreference } from '@/types';

type ResolvedTheme = 'light' | 'dark';

type ThemeContextType = {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setPreference: (next: ThemePreference) => Promise<void>;
  isSaving: boolean;
};

const STORAGE_KEY = 'dynasty-theme-preference';
const BOOTSTRAP_KEY = ['bootstrap'] as const;

const ThemeContext = createContext<ThemeContextType | null>(
  null,
);

function isThemePreference(
  value: string | null,
): value is ThemePreference {
  return value === 'light'
    || value === 'dark'
    || value === 'system';
}

function getStoredPreference(): ThemePreference {
  if (typeof window === 'undefined') {
    return 'system';
  }

  const stored = window.localStorage.getItem(
    STORAGE_KEY,
  );

  if (isThemePreference(stored)) {
    return stored;
  }

  return 'system';
}

function resolveTheme(
  preference: ThemePreference,
): ResolvedTheme {
  if (preference === 'light' || preference === 'dark') {
    return preference;
  }

  if (
    typeof window !== 'undefined'
    && window.matchMedia(
      '(prefers-color-scheme: dark)',
    ).matches
  ) {
    return 'dark';
  }

  return 'light';
}

function applyTheme(
  preference: ThemePreference,
): ResolvedTheme {
  const resolved = resolveTheme(
    preference,
  );

  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;

  return resolved;
}

export function ThemeProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const queryClient = useQueryClient();
  const bootstrap = useBootstrap();

  const bootstrapPreference = (
    bootstrap.data?.theme_preference
    ?? null
  );

  const [preference, setPreferenceState] =
    useState<ThemePreference>(
      getStoredPreference,
    );

  const [resolvedTheme, setResolvedTheme] =
    useState<ResolvedTheme>(() =>
      resolveTheme(
        getStoredPreference(),
      )
    );

  const updatePreference = useMutation({
    mutationFn: api.auth.updateThemePreference,

    onSuccess: async (_, nextPreference) => {
      queryClient.setQueryData(
        BOOTSTRAP_KEY,
        (current: Bootstrap | undefined | null) => {
          if (!current) {
            return current;
          }

          return {
            ...current,
            theme_preference: nextPreference,
          };
        },
      );

      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_KEY,
      });
    },
  });

  useEffect(() => {
    const nextPreference = (
      bootstrapPreference
      ?? getStoredPreference()
    );

    setPreferenceState(
      nextPreference,
    );

    window.localStorage.setItem(
      STORAGE_KEY,
      nextPreference,
    );

    setResolvedTheme(
      applyTheme(
        nextPreference,
      )
    );
  }, [bootstrapPreference]);

  useEffect(() => {
    if (preference !== 'system') {
      return undefined;
    }

    const media = window.matchMedia(
      '(prefers-color-scheme: dark)',
    );

    const sync = () => {
      setResolvedTheme(
        applyTheme(
          'system',
        )
      );
    };

    sync();
    media.addEventListener('change', sync);
    return () => {
      media.removeEventListener('change', sync);
    };
  }, [preference]);

  const value = useMemo<ThemeContextType>(
    () => ({
      preference,
      resolvedTheme,
      isSaving: updatePreference.isPending,
      setPreference: async (
        nextPreference,
      ) => {
        setPreferenceState(
          nextPreference,
        );

        window.localStorage.setItem(
          STORAGE_KEY,
          nextPreference,
        );

        setResolvedTheme(
          applyTheme(
            nextPreference,
          )
        );

        await updatePreference.mutateAsync(
          nextPreference,
        );
      },
    }),
    [
      bootstrapPreference,
      preference,
      resolvedTheme,
      updatePreference,
    ],
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(
    ThemeContext,
  );

  if (!context) {
    throw new Error(
      'useTheme must be used within ThemeProvider',
    );
  }

  return context;
}
