import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import {
  ACCENT_STORAGE_KEY,
  applyAccentColor,
  applyResolvedTheme,
  getStoredAccentColor,
  getStoredThemePreference,
  resolveThemePreference,
  THEME_STORAGE_KEY,
} from '@/context/theme';
import type { ThemeContextType } from '@/context/theme-context';
import { ThemeContext } from '@/context/theme-context';
import { useBootstrap } from '@/hooks/useBootstrap';
import type { AccentColor, Bootstrap, ThemePreference } from '@/types';

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

  const bootstrapAccent = (
    bootstrap.data?.accent_color
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

  const [accentColor, setAccentColorState] =
    useState<AccentColor>(
      getStoredAccentColor,
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

  const updateAccent = useMutation({
    mutationFn: api.auth.updateAccentColor,

    onSuccess: async (_, nextAccent) => {
      queryClient.setQueryData(
        BOOTSTRAP_QUERY_KEY,
        (current: Bootstrap | undefined | null) => {
          if (!current) {
            return current;
          }

          return {
            ...current,
            accent_color: nextAccent,
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
    const nextAccent = (
      bootstrapAccent
      ?? getStoredAccentColor()
    );

    setAccentColorState(nextAccent);

    window.localStorage.setItem(
      ACCENT_STORAGE_KEY,
      nextAccent,
    );

    applyAccentColor(nextAccent);
  }, [bootstrapAccent]);

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
      accentColor,
      isSaving: updatePreference.isPending,
      isSavingAccent: updateAccent.isPending,
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
      setAccentColor: async (
        nextAccent: AccentColor,
      ) => {
        setAccentColorState(nextAccent);

        window.localStorage.setItem(
          ACCENT_STORAGE_KEY,
          nextAccent,
        );

        applyAccentColor(nextAccent);

        await updateAccent.mutateAsync(
          nextAccent,
        );
      },
    }),
    [
      preference,
      resolvedTheme,
      accentColor,
      updatePreference,
      updateAccent,
    ],
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}
