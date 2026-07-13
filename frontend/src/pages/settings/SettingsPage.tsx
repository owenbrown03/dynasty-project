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
  DraftPickProjectionSettings,
  ValueBasis,
} from '@/types';
import { notify } from '@/utils/notify';
import { VALUE_BASIS_OPTIONS } from '@/pages/waivers/waiver.constants';

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
                VALUE_BASIS_OPTIONS.map((option) => (
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
          These rules determine when next-year pick slots are projected and what method is used in league draft capital sections.
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
                  start_week: (
                    draftPickProjectionSettings?.start_week
                    ?? 4
                  ),
                  method: (
                    draftPickProjectionSettings?.method
                    ?? 'max_pf'
                  ),
                });
              }}
            />
          </label>

          <label className="settings-field">
            <span>Start projecting in week</span>
            <input
              type="number"
              min={1}
              max={18}
              value={draftPickProjectionSettings?.start_week ?? 4}
              disabled={updateDraftPickProjectionSettings.isPending}
              onChange={(event) => {
                void saveDraftPickProjectionSettings({
                  enabled: (
                    draftPickProjectionSettings?.enabled
                    ?? true
                  ),
                  start_week: Number(event.target.value),
                  method: (
                    draftPickProjectionSettings?.method
                    ?? 'max_pf'
                  ),
                });
              }}
            />
          </label>
        </div>

        <div className="settings-method-list">
          {
            DRAFT_PICK_PROJECTION_METHOD_OPTIONS.map((option) => (
              <label
                key={option.value}
                className="settings-method-option"
              >
                <input
                  type="radio"
                  name="draft-pick-projection-method"
                  checked={(
                    draftPickProjectionSettings?.method
                    ?? 'max_pf'
                  ) === option.value}
                  disabled={updateDraftPickProjectionSettings.isPending}
                  onChange={() => {
                    void saveDraftPickProjectionSettings({
                      enabled: (
                        draftPickProjectionSettings?.enabled
                        ?? true
                      ),
                      start_week: (
                        draftPickProjectionSettings?.start_week
                        ?? 4
                      ),
                      method: option.value,
                    });
                  }}
                />

                <div>
                  <strong>{option.label}</strong>
                  <span>{option.description}</span>
                </div>
              </label>
            ))
          }
        </div>
      </section>
    </div>
  );
};
