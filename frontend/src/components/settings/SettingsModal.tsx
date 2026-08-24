import './SettingsModal.css';

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import { useSettingsContext } from '@/context/useSettingsContext';
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
} from '@/types';
import { notify } from '@/utils/notify';
import { getValueBasisOptions } from '@/pages/waivers/waiver.constants';

const DRAFT_PICK_PROJECTION_METHOD_OPTIONS: Array<{
  value: DraftPickProjectionMethod;
  label: string;
  description: string;
}> = [
  {
    value: 'sleeper_projection',
    label: 'Sleeper projected points',
    description: 'Ranks rosters by total sleeper projected points, then points for and projected points as tiebreakers.',
  },
  {
    value: 'ktc_redraft',
    label: 'KTC (redraft)',
    description: 'Ranks rosters by total KTC redraft value, then points for and projected points as tiebreakers.',
  },
  {
    value: 'fantasycalc_redraft',
    label: 'FantasyCalc (redraft)',
    description: 'Ranks rosters by total FantasyCalc redraft value, then points for and projected points as tiebreakers.',
  },
  {
    value: 'max_pf',
    label: 'Max PF',
    description: 'Uses cumulative potential points first, then points for and projected points as tiebreakers.',
  },
  {
    value: 'standings_proxy',
    label: 'Standings proxy',
    description: 'Uses record first, then points for and projected points as tiebreakers.',
  },
  {
    value: 'redraft_starter_war',
    label: 'Redraft starter WAR',
    description: 'Projects earlier picks to rosters with lower total redraft starter WAR.',
  },
  {
    value: 'redraft_roster_war',
    label: 'Redraft roster WAR',
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

export const SettingsModal = () => {
  const { isOpen, close } = useSettingsContext();
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

      await queryClient.invalidateQueries();
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

  if (!isOpen) return null;

  return (
    <div className="settings-modal">
      <div className="settings-modal-content">
        <button
          className="button-secondary settings-modal-close"
          onClick={close}
        >
          ×
        </button>

        <div className="settings-modal-header">
          <p className="page-eyebrow">Settings</p>
          <h1 className="settings-modal-title">Preferences</h1>
          <p className="settings-modal-description">
            Control account defaults and how the app projects future rookie picks in draft capital views.
          </p>
        </div>

        

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

          </div>
        </section>

        <section className="settings-card">
          <div className="settings-card-header">
            <div>
              <p>Dynasty</p>
              <h2>Dynasty value system</h2>
            </div>
          </div>

          <div className="settings-note">
            The market prices used for dynasty trades, waivers, and
            roster valuation everywhere on the site.
          </div>

          <div className="settings-grid">
            <label className="settings-field">
              <span>Dynasty value system</span>
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
              <p>Redraft</p>
              <h2>Redraft projection</h2>
            </div>
          </div>

          <div className="settings-note">
            Projects how rosters will finish in redraft, using the
            method you pick before the threshold week and after it.
            Set both to the same method to always use one. Future
            picks apply the ranking in reverse — the weakest
            projected roster picks first (1.01). This drives:
          </div>
          <ul className="settings-applies-list">
            <li>Advisor contention &amp; fringe-contender bands</li>
            <li>Future pick projection</li>
            <li>Season payout projection</li>
          </ul>

          <div className="settings-grid">
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
                      ?? 'sleeper_projection'
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
                      ?? 'sleeper_projection'
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
    </div>
  );
};
