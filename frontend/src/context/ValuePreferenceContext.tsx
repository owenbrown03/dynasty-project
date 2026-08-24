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
  getStoredRedraftValuePreference,
  getStoredValuePreference,
  REDRAFT_VALUE_PREFERENCE_STORAGE_KEY,
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
  const bootstrapRedraftPreference = (
    bootstrap.data?.redraft_value_preference ?? null
  );
  const [
    redraftPreference,
    setRedraftPreferenceState,
  ] = useState<ValueBasis>(
    getStoredRedraftValuePreference,
  );

  const updatePreference = useMutation({
    mutationFn: (input: {
      value_preference: ValueBasis;
      redraft_value_preference?: ValueBasis;
    }) =>
      api.auth.updateValuePreference(
        input.value_preference,
        input.redraft_value_preference,
      ),

    onSuccess: async (response) => {
      queryClient.setQueryData(
        BOOTSTRAP_QUERY_KEY,
        (current: Bootstrap | undefined | null) => {
          if (!current) {
            return current;
          }

          return {
            ...current,
            value_preference:
              response.data.value_preference,
            redraft_value_preference:
              response.data.redraft_value_preference,
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

  useEffect(() => {
    const nextRedraft = (
      bootstrapRedraftPreference
      ?? getStoredRedraftValuePreference()
    );

    setRedraftPreferenceState(nextRedraft);

    window.localStorage.setItem(
      REDRAFT_VALUE_PREFERENCE_STORAGE_KEY,
      nextRedraft,
    );
  }, [bootstrapRedraftPreference]);

  const value = useMemo<ValuePreferenceContextType>(
    () => ({
      preference,
      redraftPreference,
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

        await updatePreference.mutateAsync({
          value_preference: nextPreference,
        });
      },
      setRedraftPreference: async (
        nextRedraft: ValueBasis,
      ) => {
        setRedraftPreferenceState(nextRedraft);

        window.localStorage.setItem(
          REDRAFT_VALUE_PREFERENCE_STORAGE_KEY,
          nextRedraft,
        );

        await updatePreference.mutateAsync({
          value_preference: preference,
          redraft_value_preference: nextRedraft,
        });
      },
    }),
    [
      preference,
      redraftPreference,
      updatePreference,
    ],
  );

  return (
    <ValuePreferenceContext.Provider value={value}>
      {children}
    </ValuePreferenceContext.Provider>
  );
}
