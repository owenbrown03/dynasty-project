import './SettingsPage.css';

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useTheme } from '@/context/useTheme';
import { useValuePreference } from '@/context/useValuePreference';
import { useBootstrap } from '@/hooks/useBootstrap';
import type {
  AccentColor,
  Bootstrap,
  DraftPickProjectionMethod,
  DraftPickProjectionPhaseMethod,
  DraftPickProjectionSettings,
  ValueBasis,
  WarValueConfig,
  WarValueScope,
  WarValueSettings,
  WarValueTimeframe,
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

const DEFAULT_WAR_VALUE_SETTINGS: WarValueSettings = {
  sleeper_projection: {
    timeframe: 'dynasty',
    scope: 'roster',
  },
  my: {
    timeframe: 'dynasty',
    scope: 'roster',
  },
};

const WAR_TIMEFRAME_OPTIONS: Array<{
  value: WarValueTimeframe;
  label: string;
}> = [
  {
    value: 'dynasty',
    label: 'Dynasty',
  },
  {
    value: 'redraft',
    label: 'Redraft',
  },
];

const WAR_SCOPE_OPTIONS: Array<{
  value: WarValueScope;
  label: string;
}> = [
  {
    value: 'roster',
    label: 'Roster',
  },
  {
    value: 'starter',
    label: 'Starter',
  },
];

const ACCENT_COLOR_OPTIONS: Array<{
  value: AccentColor;
  label: string;
  lightSwatch: string;
  darkSwatch: string;
}> = [
  { value: 'blue', label: 'Blue', lightSwatch: '#1f6feb', darkSwatch: '#79a7ff' },
  { value: 'green', label: 'Green', lightSwatch: '#1f7a3f', darkSwatch: '#5ec27a' },
  { value: 'purple', label: 'Purple', lightSwatch: '#7c3aed', darkSwatch: '#a78bfa' },
  { value: 'red', label: 'Red', lightSwatch: '#b33a2b', darkSwatch: '#f18a7d' },
  { value: 'orange', label: 'Orange', lightSwatch: '#c2410c', darkSwatch: '#fb923c' },
  { value: 'teal', label: 'Teal', lightSwatch: '#0d9488', darkSwatch: '#5eead4' },
  { value: 'pink', label: 'Pink', lightSwatch: '#db2777', darkSwatch: '#f472b6' },
];

function updateWarConfig(
  settings: WarValueSettings,
  key: keyof WarValueSettings,
  patch: Partial<WarValueConfig>,
): WarValueSettings {
  return {
    ...settings,
    [key]: {
      ...settings[key],
      ...patch,
    },
  };
}

export const SettingsPage = () => {
  const queryClient = useQueryClient();
  const bootstrap = useBootstrap();
  const theme = useTheme();
  const valuePreference = useValuePreference();
  const draftPickProjectionSettings = (
    bootstrap.data?.draft_pick_projection_settings
  );
  const warValueSettings = (
    bootstrap.data?.war_value_settings
    ?? DEFAULT_WAR_VALUE_SETTINGS
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

  const updateWarValueSettings = useMutation({
    mutationFn: api.auth.updateWarValueSettings,
    onSuccess: async (response) => {
      queryClient.setQueryData(
        BOOTSTRAP_QUERY_KEY,
        (current: Bootstrap | undefined | null) => {
          if (!current) {
            return current;
          }

          return {
            ...current,
            war_value_settings: response.data.settings,
          };
        },
      );

      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });
      notify.success('WAR value settings saved.');
    },
    onError: () => {
      notify.error('Unable to save WAR value settings.');
    },
  });

  const saveDraftPickProjectionSettings = async (
    nextSettings: DraftPickProjectionSettings,
  ) => {
    await updateDraftPickProjectionSettings.mutateAsync(
      nextSettings,
    );
  };

  const saveWarValueSettings = async (
    nextSettings: WarValueSettings,
  ) => {
    await updateWarValueSettings.mutateAsync(
      nextSettings,
    );
  };

  return (
    <div className="settings-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Settings</p>
          <h1 className="page-title">Preferences</h1>
          <p className="page-description">
            Control account defaults and how the app projects future rookie picks in draft capital views.
          </p>
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-card-header">
          <div>
            <p>WAR</p>
            <h2>Value basis mapping</h2>
          </div>
        </div>

        <div className="settings-grid">
          <div className="settings-field">
            <span>Sleeper projection WAR</span>

            <div className="settings-inline-controls">
              <select
                value={warValueSettings.sleeper_projection.timeframe}
                disabled={updateWarValueSettings.isPending}
                onChange={(event) => {
                  void saveWarValueSettings(
                    updateWarConfig(
                      warValueSettings,
                      'sleeper_projection',
                      {
                        timeframe: event.target.value as WarValueTimeframe,
                      },
                    ),
                  );
                }}
              >
                {
                  WAR_TIMEFRAME_OPTIONS.map((option) => (
                    <option
                      key={option.value}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ))
                }
              </select>

              <select
                value={warValueSettings.sleeper_projection.scope}
                disabled={updateWarValueSettings.isPending}
                onChange={(event) => {
                  void saveWarValueSettings(
                    updateWarConfig(
                      warValueSettings,
                      'sleeper_projection',
                      {
                        scope: event.target.value as WarValueScope,
                      },
                    ),
                  );
                }}
              >
                {
                  WAR_SCOPE_OPTIONS.map((option) => (
                    <option
                      key={option.value}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ))
                }
              </select>
            </div>
          </div>

          <div className="settings-field">
            <span>My WAR</span>

            <div className="settings-inline-controls">
              <select
                value={warValueSettings.my.timeframe}
                disabled={updateWarValueSettings.isPending}
                onChange={(event) => {
                  void saveWarValueSettings(
                    updateWarConfig(
                      warValueSettings,
                      'my',
                      {
                        timeframe: event.target.value as WarValueTimeframe,
                      },
                    ),
                  );
                }}
              >
                {
                  WAR_TIMEFRAME_OPTIONS.map((option) => (
                    <option
                      key={option.value}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ))
                }
              </select>

              <select
                value={warValueSettings.my.scope}
                disabled={updateWarValueSettings.isPending}
                onChange={(event) => {
                  void saveWarValueSettings(
                    updateWarConfig(
                      warValueSettings,
                      'my',
                      {
                        scope: event.target.value as WarValueScope,
                      },
                    ),
                  );
                }}
              >
                {
                  WAR_SCOPE_OPTIONS.map((option) => (
                    <option
                      key={option.value}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ))
                }
              </select>
            </div>
          </div>
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

          <div className="settings-field">
            <span>Accent color</span>
            <div className="settings-accent-grid">
              {ACCENT_COLOR_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`settings-accent-swatch ${theme.accentColor === option.value ? 'settings-accent-swatch--active' : ''}`}
                  style={{
                    background: theme.resolvedTheme === 'dark'
                      ? option.darkSwatch
                      : option.lightSwatch,
                  }}
                  disabled={theme.isSavingAccent}
                  title={option.label}
                  onClick={() => {
                    void theme.setAccentColor(option.value);
                  }}
                />
              ))}
            </div>
          </div>

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
