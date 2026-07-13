import './SettingsPage.css';

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useTheme } from '@/context/useTheme';
import { useValuePreference } from '@/context/useValuePreference';
import { useBootstrap } from '@/hooks/useBootstrap';
import type {
  Bootstrap,
  DraftPickProjectionMethod,
  DraftPickProjectionPhaseMethod,
  DraftPickProjectionSettings,
  ValueBasis,
} from '@/types';
import { notify } from '@/utils/notify';
import { getValueBasisOptions } from '@/pages/waivers/waiver.constants';

const DRAFT_PICK_PROJECTION_METHOD_OPTIONS: Array<{
  value: DraftPickProjectionMethod;
  label: string;
  description: string;
}> = [
  {
    value: 'max_pf',
    label: 'Reverse max PF',
    description: 'Uses cumulative potential points first, then points for and projected points as tiebreakers.',
  },
  {
    value: 'reverse_standings',
    label: 'Reverse standings proxy',
    description: 'Uses record first, then points for and projected points as tiebreakers.',
  },
  {
    value: 'redraft_starter_war',
    label: 'Reverse redraft starter WAR',
    description: 'Projects earlier picks to rosters with lower total redraft starter WAR.',
  },
  {
    value: 'redraft_roster_war',
    label: 'Reverse redraft roster WAR',
    description: 'Projects earlier picks to rosters with lower total redraft roster WAR.',
  },
];

const DRAFT_PICK_PRE_SWITCH_OPTIONS: Array<{
  value: DraftPickProjectionPhaseMethod;
  label: string;
}> = [
  {
    value: 'none',
    label: 'No projection',
  },
  ...DRAFT_PICK_PROJECTION_METHOD_OPTIONS.map((option) => ({
    value: option.value,
    label: option.label,
  })),
];

export const SettingsPage = () => {
  const queryClient = useQueryClient();
  const bootstrap = useBootstrap();
  const theme = useTheme();
  const valuePreference = useValuePreference();
  const draftPickProjectionSettings = (
    bootstrap.data?.draft_pick_projection_settings
  );

  const updateDraftPickProjectionSettings = useMutation({
    mutationFn: api.auth.updateDraftPickProjectionSettings,
    onSuccess: async (response) => {
      queryClient.setQueryData(
        BOOTSTRAP_QUERY_KEY,
        (current: Bootstrap | undefined | null) => {
          if (!current) {
            return current;
          }

          return {
            ...current,
            draft_pick_projection_settings: response.data.settings,
          };
        },
      );

      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });
      notify.success('Draft pick projection settings saved.');
    },
    onError: () => {
      notify.error('Unable to save draft pick projection settings.');
    },
  });

  const saveDraftPickProjectionSettings = async (
    nextSettings: DraftPickProjectionSettings,
  ) => {
    await updateDraftPickProjectionSettings.mutateAsync(
      nextSettings,
    );
  };

  return (
    <div className="settings-page">
      <section className="settings-page-header">
        <div>
          <p className="page-eyebrow">Settings</p>
          <h1 className="settings-page-title">Preferences</h1>
          <p className="settings-page-description">
            Control account defaults and how the app projects future rookie picks in draft capital views.
          </p>
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-card-header">
          <div>
            <p>Display</p>
            <h2>Account defaults</h2>
          </div>
        </div>

        <div className="settings-grid">
          <label className="settings-field">
            <span>Theme</span>
            <select
              value={theme.preference}
              onChange={(event) => {
                void theme.setPreference(
                  event.target.value as
                    | 'light'
                    | 'dark'
                    | 'system',
                );
              }}
              disabled={theme.isSaving}
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="system">System</option>
            </select>
          </label>

          <label className="settings-field">
            <span>Default value basis</span>
            <select
              value={valuePreference.preference}
              onChange={(event) => {
                void valuePreference.setPreference(
                  event.target.value as ValueBasis,
                );
              }}
              disabled={valuePreference.isSaving}
            >
              {
                getValueBasisOptions(
                  bootstrap.data?.authenticated ?? false,
                ).map((option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ))
              }
            </select>
          </label>
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-card-header">
          <div>
            <p>Draft picks</p>
            <h2>Future pick projection</h2>
          </div>
        </div>

        <div className="settings-note">
          These rules determine whether next-year pick slots are projected, what method is used before a threshold week, and what method is used after that threshold.
        </div>

        <div className="settings-grid">
          <label className="settings-field settings-toggle-field">
            <span>Enable projections</span>
            <input
              type="checkbox"
              checked={draftPickProjectionSettings?.enabled ?? true}
              disabled={updateDraftPickProjectionSettings.isPending}
              onChange={(event) => {
                void saveDraftPickProjectionSettings({
                  enabled: event.target.checked,
                  switch_week: (
                    draftPickProjectionSettings?.switch_week
                    ?? 4
                  ),
                  before_week_method: (
                    draftPickProjectionSettings?.before_week_method
                    ?? 'none'
                  ),
                  from_week_method: (
                    draftPickProjectionSettings?.from_week_method
                    ?? 'max_pf'
                  ),
                });
              }}
            />
          </label>

          <label className="settings-field">
            <span>Switch methods in week</span>
            <input
              type="number"
              min={1}
              max={18}
              value={draftPickProjectionSettings?.switch_week ?? 4}
              disabled={updateDraftPickProjectionSettings.isPending}
              onChange={(event) => {
                void saveDraftPickProjectionSettings({
                  enabled: (
                    draftPickProjectionSettings?.enabled
                    ?? true
                  ),
                  switch_week: Number(event.target.value),
                  before_week_method: (
                    draftPickProjectionSettings?.before_week_method
                    ?? 'none'
                  ),
                  from_week_method: (
                    draftPickProjectionSettings?.from_week_method
                    ?? 'max_pf'
                  ),
                });
              }}
            />
          </label>
        </div>

        <div className="settings-grid">
          <label className="settings-field">
            <span>Before week {draftPickProjectionSettings?.switch_week ?? 4}</span>
            <select
              value={draftPickProjectionSettings?.before_week_method ?? 'none'}
              disabled={updateDraftPickProjectionSettings.isPending}
              onChange={(event) => {
                void saveDraftPickProjectionSettings({
                  enabled: (
                    draftPickProjectionSettings?.enabled
                    ?? true
                  ),
                  switch_week: (
                    draftPickProjectionSettings?.switch_week
                    ?? 4
                  ),
                  before_week_method: (
                    event.target.value as DraftPickProjectionPhaseMethod
                  ),
                  from_week_method: (
                    draftPickProjectionSettings?.from_week_method
                    ?? 'max_pf'
                  ),
                });
              }}
            >
              {
                DRAFT_PICK_PRE_SWITCH_OPTIONS.map((option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ))
              }
            </select>
          </label>

          <label className="settings-field">
            <span>Week {draftPickProjectionSettings?.switch_week ?? 4} and later</span>
            <select
              value={draftPickProjectionSettings?.from_week_method ?? 'max_pf'}
              disabled={updateDraftPickProjectionSettings.isPending}
              onChange={(event) => {
                void saveDraftPickProjectionSettings({
                  enabled: (
                    draftPickProjectionSettings?.enabled
                    ?? true
                  ),
                  switch_week: (
                    draftPickProjectionSettings?.switch_week
                    ?? 4
                  ),
                  before_week_method: (
                    draftPickProjectionSettings?.before_week_method
                    ?? 'none'
                  ),
                  from_week_method: (
                    event.target.value as DraftPickProjectionMethod
                  ),
                });
              }}
            >
              {
                DRAFT_PICK_PROJECTION_METHOD_OPTIONS.map((option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ))
              }
            </select>
          </label>
        </div>

        <div className="settings-method-list">
          {
            DRAFT_PICK_PROJECTION_METHOD_OPTIONS.map((option) => (
              <div
                key={option.value}
                className="settings-method-option"
              >
                <span
                  className="settings-method-swatch"
                  aria-hidden="true"
                />

                <div>
                  <strong>{option.label}</strong>
                  <span>{option.description}</span>
                </div>
              </div>
            ))
          }
        </div>
      </section>
    </div>
  );
};
