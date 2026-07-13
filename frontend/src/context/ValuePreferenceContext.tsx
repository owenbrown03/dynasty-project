import {
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useBootstrap } from '@/hooks/useBootstrap';
import {
  getStoredValuePreference,
  VALUE_PREFERENCE_STORAGE_KEY,
} from '@/context/value-preference';
import {
  ValuePreferenceContext,
  type ValuePreferenceContextType,
} from '@/context/value-preference-context';
import type {
  Bootstrap,
  ValueBasis,
} from '@/types';

export function ValuePreferenceProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const queryClient = useQueryClient();
  const bootstrap = useBootstrap();

  const bootstrapPreference = (
    bootstrap.data?.value_preference
    ?? null
  );

  const [preference, setPreferenceState] =
    useState<ValueBasis>(
      getStoredValuePreference,
    );

  const updatePreference = useMutation({
    mutationFn: api.auth.updateValuePreference,

    onSuccess: async (_, nextPreference) => {
      queryClient.setQueryData(
        BOOTSTRAP_QUERY_KEY,
        (current: Bootstrap | undefined | null) => {
          if (!current) {
            return current;
          }

          return {
            ...current,
            value_preference: nextPreference,
          };
        },
      );

      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });
    },
  });

  useEffect(() => {
    let nextPreference = (
      bootstrapPreference
      ?? getStoredValuePreference()
    );

    if (
      nextPreference === 'my_war'
      && bootstrap.data?.authenticated !== true
    ) {
      nextPreference = 'ktc';
    }

    setPreferenceState(
      nextPreference,
    );

    window.localStorage.setItem(
      VALUE_PREFERENCE_STORAGE_KEY,
      nextPreference,
    );
  }, [bootstrap.data?.authenticated, bootstrapPreference]);

  const value = useMemo<ValuePreferenceContextType>(
    () => ({
      preference,
      isSaving: updatePreference.isPending,
      setPreference: async (
        nextPreference: ValueBasis,
      ) => {
        setPreferenceState(
          nextPreference,
        );

        window.localStorage.setItem(
          VALUE_PREFERENCE_STORAGE_KEY,
          nextPreference,
        );

        await updatePreference.mutateAsync(
          nextPreference,
        );
      },
    }),
    [preference, updatePreference],
  );

  return (
    <ValuePreferenceContext.Provider value={value}>
      {children}
    </ValuePreferenceContext.Provider>
  );
}
