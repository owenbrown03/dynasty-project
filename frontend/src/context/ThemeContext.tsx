import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import {
  applyResolvedTheme,
  getStoredThemePreference,
  resolveThemePreference,
  THEME_STORAGE_KEY,
} from '@/context/theme';
import type { ThemeContextType } from '@/context/theme-context';
import { ThemeContext } from '@/context/theme-context';
import { useBootstrap } from '@/hooks/useBootstrap';
import type { Bootstrap, ThemePreference } from '@/types';

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
      getStoredThemePreference,
    );

  const [resolvedTheme, setResolvedTheme] =
    useState(() =>
      resolveThemePreference(
        getStoredThemePreference(),
      )
    );

  const updatePreference = useMutation({
    mutationFn: api.auth.updateThemePreference,

    onSuccess: async (_, nextPreference) => {
      queryClient.setQueryData(
        BOOTSTRAP_QUERY_KEY,
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
        queryKey: BOOTSTRAP_QUERY_KEY,
      });
    },
  });

  useEffect(() => {
    const nextPreference = (
      bootstrapPreference
      ?? getStoredThemePreference()
    );

    setPreferenceState(
      nextPreference,
    );

    window.localStorage.setItem(
      THEME_STORAGE_KEY,
      nextPreference,
    );

    setResolvedTheme(
      applyResolvedTheme(
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
        applyResolvedTheme(
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
        nextPreference: ThemePreference,
      ) => {
        setPreferenceState(
          nextPreference,
        );

        window.localStorage.setItem(
          THEME_STORAGE_KEY,
          nextPreference,
        );

        setResolvedTheme(
          applyResolvedTheme(
            nextPreference,
          )
        );

        await updatePreference.mutateAsync(
          nextPreference,
        );
      },
    }),
    [
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
