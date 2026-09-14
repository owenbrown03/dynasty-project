import { useState, useMemo, useEffect } from 'react';
import { AlertTriangle, Info, X } from 'lucide-react';
import {
  useCommissionerWaiversOverview,
  useUpdateCommissionerWaivers,
  useCommissionerWaiversPreset,
  useSaveCommissionerWaiversPreset,
  useResetCommissionerWaiversPreset,
} from '@/hooks/sleeper/useUsers';
import { notify } from '@/utils/notify';
import { Skeleton } from '@/components/feedback/Skeleton';
import type { CommissionerWaiverLeagueInfo } from '@/api/v1/endpoints/sleeper/user.endpoints';

// Standard In-Season default: [Sun=3 (Waivers->FA), Mon=0 (FA), Tue=1 (Waivers), Wed=1 (Waivers), Thu=3 (Waivers->FA), Fri=3 (Waivers->FA), Sat=3 (Waivers->FA)]
const DEFAULT_STANDARD_PRESET = [3, 0, 1, 1, 3, 3, 3];

// Standard Off-Season default: [Sun=2 (Locked), Mon=2 (Locked), Tue=2 (Locked), Wed=1 (Waivers), Thu=2 (Locked), Fri=2 (Locked), Sat=2 (Locked)]
const DEFAULT_OFFSEASON_PRESET = [2, 2, 2, 1, 2, 2, 2];

interface PresetMatch {
  label: string;
  variant: 'inseason' | 'offseason' | 'other';
}

function getLeaguePresetMatch(
  league: CommissionerWaiverLeagueInfo,
  inSeasonDays: number[],
  offSeasonDays: number[],
): PresetMatch | null {
  if (!league.daily_waivers) return null;
  const days = league.schedule.map((s) => s.setting);
  if (days.length !== 7) return null;

  const matches = (target: number[]) => days.every((v, i) => v === target[i]);

  if (matches(inSeasonDays)) {
    return { label: 'Standard In-Season', variant: 'inseason' };
  }
  if (matches(offSeasonDays)) {
    return { label: 'Standard Off-Season', variant: 'offseason' };
  }
  if (matches([1, 1, 1, 1, 1, 1, 1])) {
    return { label: 'All Waivers', variant: 'other' };
  }
  if (matches([0, 0, 0, 0, 0, 0, 0])) {
    return { label: 'All FA', variant: 'other' };
  }
  if (matches([3, 3, 3, 3, 3, 3, 3])) {
    return { label: 'All Waivers → FA', variant: 'other' };
  }
  if (matches([2, 2, 2, 2, 2, 2, 2])) {
    return { label: 'Lock All', variant: 'other' };
  }
  return null;
}

// 0=FA, 1=Waivers, 2=Locked, 3=Waivers->FA
const WAIVER_OPTIONS = [
  { value: 1, label: 'Waivers', shortLabel: 'Waivers', colorClass: 'badge-waivers' },
  { value: 0, label: 'Free Agent (FA)', shortLabel: 'FA', colorClass: 'badge-fa' },
  { value: 3, label: 'Waivers → FA', shortLabel: 'Waivers → FA', colorClass: 'badge-waiver-fa' },
  { value: 2, label: 'Locked', shortLabel: 'Locked', colorClass: 'badge-locked' },
] as const;

const DAYS_OF_WEEK = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
] as const;

const HOURS_OF_DAY = [
  { value: 0, label: '12:00 AM (Midnight)' },
  { value: 1, label: '1:00 AM' },
  { value: 2, label: '2:00 AM' },
  { value: 3, label: '3:00 AM' },
  { value: 4, label: '4:00 AM' },
  { value: 5, label: '5:00 AM' },
  { value: 6, label: '6:00 AM' },
  { value: 7, label: '7:00 AM' },
  { value: 8, label: '8:00 AM' },
  { value: 9, label: '9:00 AM' },
  { value: 10, label: '10:00 AM' },
  { value: 11, label: '11:00 AM' },
  { value: 12, label: '12:00 PM (Noon)' },
  { value: 13, label: '1:00 PM' },
  { value: 14, label: '2:00 PM' },
  { value: 15, label: '3:00 PM' },
  { value: 16, label: '4:00 PM' },
  { value: 17, label: '5:00 PM' },
  { value: 18, label: '6:00 PM' },
  { value: 19, label: '7:00 PM' },
  { value: 20, label: '8:00 PM' },
  { value: 21, label: '9:00 PM' },
  { value: 22, label: '10:00 PM' },
  { value: 23, label: '11:00 PM' },
];

const WAIVER_CLEAR_DAYS_OPTIONS = [
  { value: 0, label: '0 Days (No hold)' },
  { value: 1, label: '1 Day' },
  { value: 2, label: '2 Days (Standard)' },
  { value: 3, label: '3 Days' },
];

const WAIVER_AFTER_GAMES_OPTIONS = [
  { value: 0, label: 'None' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday (Standard)' },
  { value: 3, label: 'Thursday' },
];

function formatHour(hour: number): string {
  const match = HOURS_OF_DAY.find((h) => h.value === hour);
  return match ? match.label : `${hour}:00`;
}

function formatAfterGamesDay(val: number): string {
  if (val === 0) return 'None';
  const match = WAIVER_AFTER_GAMES_OPTIONS.find((o) => o.value === val);
  return match ? match.label.split(' ')[0] : 'Wed';
}

function getOptionLabel(setting: number): string {
  const match = WAIVER_OPTIONS.find((o) => o.value === setting);
  return match ? match.shortLabel : 'Waivers';
}

function getOptionBadgeClass(setting: number): string {
  const match = WAIVER_OPTIONS.find((o) => o.value === setting);
  return match ? match.colorClass : 'badge-waivers';
}

export const CommissionerWaiversTab = () => {
  const {
    data: leagues = [],
    isLoading,
    isFetching,
    error,
    refetch,
  } = useCommissionerWaiversOverview();
  const updateMutation = useUpdateCommissionerWaivers();
  const { data: inSeasonPreset } = useCommissionerWaiversPreset('inseason');
  const { data: offSeasonPreset } = useCommissionerWaiversPreset('offseason');
  const savePresetMutation = useSaveCommissionerWaiversPreset();
  const resetPresetMutation = useResetCommissionerWaiversPreset();

  const [search, setSearch] = useState('');
  const [selectedLeagues, setSelectedLeagues] = useState<Set<string>>(new Set());

  // Configuration state
  const [dailyWaiversEnabled, setDailyWaiversEnabled] = useState(true);
  const [processingHour, setProcessingHour] = useState<number | 'keep'>('keep');
  const [waiverDayOfWeek, setWaiverDayOfWeek] = useState<number | 'keep'>('keep');
  const [waiverClearDays, setWaiverClearDays] = useState<number | 'keep'>('keep');
  const [showInfoModal, setShowInfoModal] = useState(false);

  // Sunday to Saturday schedule (indices 0..6: Sun, Mon, Tue, Wed, Thu, Fri, Sat)
  const [schedule, setSchedule] = useState<number[]>(DEFAULT_STANDARD_PRESET);
  const [hasUserEditedSchedule, setHasUserEditedSchedule] = useState(false);

  // Sync custom in-season preset from account once loaded if user hasn't started manually editing
  useEffect(() => {
    if (inSeasonPreset?.sunday_to_saturday_settings && !hasUserEditedSchedule) {
      setSchedule((prev) => {
        const next = inSeasonPreset.sunday_to_saturday_settings;
        if (prev.length === next.length && prev.every((v, i) => v === next[i])) {
          return prev;
        }
        return next;
      });
      if (inSeasonPreset.daily_waivers !== undefined) {
        setDailyWaiversEnabled((prev) => {
          const next = Boolean(inSeasonPreset.daily_waivers);
          return prev === next ? prev : next;
        });
      }
    }
  }, [inSeasonPreset, hasUserEditedSchedule]);

  const filteredLeagues = useMemo(() => {
    return leagues.filter((league) => {
      const matchSearch = league.league_name.toLowerCase().includes(search.toLowerCase());
      return matchSearch;
    });
  }, [leagues, search]);

  const handleSelectAll = () => {
    setSelectedLeagues(new Set(filteredLeagues.map((l) => l.league_id)));
  };

  const handleSelectNone = () => {
    setSelectedLeagues(new Set());
  };

  const toggleLeague = (id: string) => {
    const next = new Set(selectedLeagues);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedLeagues(next);
  };

  const updateDaySetting = (dayIndex: number, value: number) => {
    setHasUserEditedSchedule(true);
    setSchedule((prev) => {
      const next = [...prev];
      next[dayIndex] = value;
      return next;
    });
  };

  // Presets
  const applyPreset = (presetSchedule: number[]) => {
    setHasUserEditedSchedule(true);
    setSchedule(presetSchedule);
  };

  const applyStandardInSeasonPreset = () => {
    setHasUserEditedSchedule(true);
    const targetSchedule = inSeasonPreset?.sunday_to_saturday_settings || DEFAULT_STANDARD_PRESET;
    setSchedule(targetSchedule);
    if (inSeasonPreset?.daily_waivers !== undefined) {
      setDailyWaiversEnabled(Boolean(inSeasonPreset.daily_waivers));
    }
  };

  const applyStandardOffSeasonPreset = () => {
    setHasUserEditedSchedule(true);
    const targetSchedule = offSeasonPreset?.sunday_to_saturday_settings || DEFAULT_OFFSEASON_PRESET;
    setSchedule(targetSchedule);
    if (offSeasonPreset?.daily_waivers !== undefined) {
      setDailyWaiversEnabled(Boolean(offSeasonPreset.daily_waivers));
    }
  };

  const handleSaveInSeasonPreset = async () => {
    try {
      await savePresetMutation.mutateAsync({
        sunday_to_saturday_settings: schedule,
        daily_waivers_hour: processingHour === 'keep' ? null : processingHour,
        daily_waivers: dailyWaiversEnabled ? 1 : 0,
        presetType: 'inseason',
      });
      notify.success('Standard In-Season preset saved to your account!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save preset';
      notify.error(msg);
    }
  };

  const handleResetInSeasonPreset = async () => {
    try {
      await resetPresetMutation.mutateAsync('inseason');
      setSchedule(DEFAULT_STANDARD_PRESET);
      notify.success('Standard In-Season preset reset to default.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reset preset';
      notify.error(msg);
    }
  };

  const handleSaveOffSeasonPreset = async () => {
    try {
      await savePresetMutation.mutateAsync({
        sunday_to_saturday_settings: schedule,
        daily_waivers_hour: processingHour === 'keep' ? null : processingHour,
        daily_waivers: dailyWaiversEnabled ? 1 : 0,
        presetType: 'offseason',
      });
      notify.success('Standard Off-Season preset saved to your account!');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save preset';
      notify.error(msg);
    }
  };

  const handleResetOffSeasonPreset = async () => {
    try {
      await resetPresetMutation.mutateAsync('offseason');
      setSchedule(DEFAULT_OFFSEASON_PRESET);
      notify.success('Standard Off-Season preset reset to default.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reset preset';
      notify.error(msg);
    }
  };


  const handleUpdate = async () => {
    if (selectedLeagues.size === 0) return;

    const hourText = processingHour === 'keep' ? 'Retain current hour' : formatHour(processingHour);
    const modeText = dailyWaiversEnabled ? 'Enabled' : 'Disabled';
    const scheduleSummary = DAYS_OF_WEEK.map((d, i) => `${d.slice(0, 3)}: ${getOptionLabel(schedule[i])}`).join(', ');

    const confirmed = window.confirm(
      `Update Custom Waivers for ${selectedLeagues.size} league(s)?\n\n` +
      `Daily Waivers: ${modeText}\n` +
      `Processing Time: ${hourText}\n` +
      `Schedule: ${scheduleSummary}`
    );
    if (!confirmed) return;

    try {
      const res = await updateMutation.mutateAsync({
        league_ids: Array.from(selectedLeagues),
        daily_waivers: dailyWaiversEnabled ? 1 : 0,
        sunday_to_saturday_settings: schedule,
        daily_waivers_hour: processingHour === 'keep' ? null : processingHour,
        waiver_clear_days: waiverClearDays === 'keep' ? null : waiverClearDays,
        waiver_day_of_week: waiverDayOfWeek === 'keep' ? null : waiverDayOfWeek,
      });

      const failures = (res.results || []).filter((r) => !r.success);
      if (failures.length > 0) {
        const errorDetails = failures
          .map((f) => `${f.league_name}: ${f.error || 'Failed'}`)
          .join('; ');
        notify.error(`Updated with some errors: ${errorDetails}`);
      } else {
        notify.success(`Successfully updated waiver settings for ${res.successful_leagues} league(s)!`);
        setSelectedLeagues(new Set());
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update waiver settings';
      notify.error(message);
    }
  };

  if (isLoading) {
    return (
      <div className="commissioner-empty-state">
        <Skeleton width={240} height={24} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="commissioner-empty-state">
        Error loading commissioner leagues: {error.message}
      </div>
    );
  }

  return (
    <div className="commissioner-waivers-tab">
      {/* Top Configuration Box */}
      <section className="commissioner-waivers-config-card">
        <div className="config-header">
          <div>
            <div className="config-title-row">
              <h3 className="config-title">Allow Custom Daily Waivers</h3>
              <button
                type="button"
                className="info-circle-btn"
                onClick={() => setShowInfoModal(true)}
                title="What is Allow Custom Daily Waivers?"
                aria-label="Allow Custom Daily Waivers Information"
              >
                <Info size={14} />
              </button>
            </div>
            <p className="config-subtitle">
              Configure daily waiver behavior across Sunday through Saturday. Custom daily waivers will be enabled for all selected leagues.
            </p>
          </div>
          <div className="config-actions">
            <button
              type="button"
              className="button-primary"
              disabled={selectedLeagues.size === 0 || updateMutation.isPending}
              onClick={handleUpdate}
            >
              {updateMutation.isPending
                ? 'Applying Settings...'
                : !dailyWaiversEnabled
                ? `Disable on ${selectedLeagues.size} Selected League${selectedLeagues.size === 1 ? '' : 's'}`
                : `Apply to ${selectedLeagues.size} Selected League${selectedLeagues.size === 1 ? '' : 's'}`}
            </button>
          </div>
        </div>

        {/* Global Controls: Processing Hour + Drop Hold + Clear Day + Presets */}
        <div className="config-row-controls">
          <div className="control-group">
            <span className="control-label">Daily Processing Time</span>
            <select
              value={processingHour}
              onChange={(e) => {
                const val = e.target.value;
                setProcessingHour(val === 'keep' ? 'keep' : Number(val));
              }}
              className="hour-select"
            >
              <option value="keep">Keep Current League Setting (Default)</option>
              {HOURS_OF_DAY.map((h) => (
                <option key={h.value} value={h.value}>
                  {h.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <span className="control-label">After Games Waivers Clear</span>
            <select
              value={waiverDayOfWeek}
              onChange={(e) => {
                const val = e.target.value;
                setWaiverDayOfWeek(val === 'keep' ? 'keep' : Number(val));
              }}
              className="hour-select"
            >
              <option value="keep">Keep Current League Setting (Default)</option>
              {WAIVER_AFTER_GAMES_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <span className="control-label">Time on Waivers After Drop</span>
            <select
              value={waiverClearDays}
              onChange={(e) => {
                const val = e.target.value;
                setWaiverClearDays(val === 'keep' ? 'keep' : Number(val));
              }}
              className="hour-select"
            >
              <option value="keep">Keep Current League Setting (Default)</option>
              {WAIVER_CLEAR_DAYS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group presets-group">
            <span className="control-label">Quick Presets</span>
            <div className="preset-buttons">
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={applyStandardInSeasonPreset}
                title={
                  inSeasonPreset?.is_custom
                    ? 'Customized standard in-season schedule mapped to your account'
                    : 'System default standard in-season schedule'
                }
              >
                Standard In-Season {inSeasonPreset?.is_custom ? '(Custom)' : ''}
              </button>
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={applyStandardOffSeasonPreset}
                title={
                  offSeasonPreset?.is_custom
                    ? 'Customized standard off-season schedule mapped to your account'
                    : 'System default standard off-season schedule (Wed Waivers, other days locked)'
                }
              >
                Standard Off-Season {offSeasonPreset?.is_custom ? '(Custom)' : ''}
              </button>
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={() => applyPreset([1, 1, 1, 1, 1, 1, 1])}
                title="All days set to regular Waivers"
              >
                All Waivers
              </button>
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={() => applyPreset([0, 0, 0, 0, 0, 0, 0])}
                title="All days set to Free Agents"
              >
                All FA
              </button>
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={() => applyPreset([3, 3, 3, 3, 3, 3, 3])}
                title="Waivers process then Free Agency each day"
              >
                All Waivers → FA
              </button>
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={() => applyPreset([2, 2, 2, 2, 2, 2, 2])}
                title="All days locked"
              >
                Lock All
              </button>
              <button
                type="button"
                className={`button-secondary btn-sm ${!dailyWaiversEnabled ? 'active' : ''}`}
                onClick={() => setDailyWaiversEnabled(false)}
                title="Disable custom daily waivers and revert selected leagues to standard Sleeper weekly waiver rules"
              >
                Turn Off Daily Waivers
              </button>
            </div>
          </div>
        </div>

        {/* Warning banner when user chooses to turn off daily waivers */}
        {!dailyWaiversEnabled && (
          <div className="daily-waivers-disabled-banner">
            <div className="daily-waivers-disabled-message">
              <AlertTriangle size={15} style={{ flexShrink: 0 }} />
              <span>
                Custom daily waivers will be <strong>disabled</strong> on selected leagues (reverting to standard weekly Sleeper waiver rules).
              </span>
            </div>
            <button
              type="button"
              className="btn-link"
              onClick={() => setDailyWaiversEnabled(true)}
            >
              Re-enable Custom Waivers
            </button>
          </div>
        )}

        {/* Standard In-Season Customization Bar */}
        <div className="standard-preset-bar">
          <div className="standard-preset-status">
            <span className="standard-preset-label">Account Standard In-Season:</span>
            {inSeasonPreset?.is_custom ? (
              <span className="preset-custom-badge">Customized</span>
            ) : (
              <span className="preset-default-badge">System Default</span>
            )}
          </div>
          <div className="standard-preset-buttons">
            <button
              type="button"
              className="button-secondary btn-sm"
              onClick={handleSaveInSeasonPreset}
              disabled={savePresetMutation.isPending}
              title="Save the current schedule below as your account's Standard In-Season preset"
            >
              {savePresetMutation.isPending ? 'Saving...' : 'Save as In-Season'}
            </button>
            {inSeasonPreset?.is_custom && (
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={handleResetInSeasonPreset}
                disabled={resetPresetMutation.isPending}
                title="Reset your custom Standard In-Season preset back to system default"
              >
                {resetPresetMutation.isPending ? 'Resetting...' : 'Reset to Default'}
              </button>
            )}
          </div>
        </div>

        {/* Standard Off-Season Customization Bar */}
        <div className="standard-preset-bar">
          <div className="standard-preset-status">
            <span className="standard-preset-label">Account Standard Off-Season:</span>
            {offSeasonPreset?.is_custom ? (
              <span className="preset-custom-badge">Customized</span>
            ) : (
              <span className="preset-default-badge">System Default</span>
            )}
          </div>
          <div className="standard-preset-buttons">
            <button
              type="button"
              className="button-secondary btn-sm"
              onClick={handleSaveOffSeasonPreset}
              disabled={savePresetMutation.isPending}
              title="Save the current schedule below as your account's Standard Off-Season preset"
            >
              {savePresetMutation.isPending ? 'Saving...' : 'Save as Off-Season'}
            </button>
            {offSeasonPreset?.is_custom && (
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={handleResetOffSeasonPreset}
                disabled={resetPresetMutation.isPending}
                title="Reset your custom Standard Off-Season preset back to system default"
              >
                {resetPresetMutation.isPending ? 'Resetting...' : 'Reset to Default'}
              </button>
            )}
          </div>
        </div>

        {/* 7-Day Grid: Sunday to Saturday */}
        <div className="schedule-days-grid">
          {DAYS_OF_WEEK.map((dayName, idx) => {
            const currentVal = schedule[idx];
            return (
              <div key={dayName} className="schedule-day-card">
                <div className="day-name">{dayName}</div>
                <div className="day-options">
                  {WAIVER_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      className={`day-opt-btn ${opt.colorClass} ${currentVal === opt.value ? 'selected' : ''}`}
                      onClick={() => updateDaySetting(idx, opt.value)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Leagues Toolbar */}
      <div className="commissioner-waivers-leagues-toolbar">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search commissioner leagues..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="selection-buttons">
          <button
            type="button"
            className="button-secondary"
            onClick={handleSelectAll}
          >
            Select All ({filteredLeagues.length})
          </button>
          <button
            type="button"
            className="button-secondary"
            onClick={handleSelectNone}
          >
            Select None
          </button>
          <button
            type="button"
            className="button-secondary"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            {isFetching ? 'Refreshing...' : 'Refresh Status'}
          </button>
        </div>
      </div>

      {/* League Selection List */}
      <div className="commissioner-waivers-league-list">
        {filteredLeagues.map((league) => {
          const isSelected = selectedLeagues.has(league.league_id);
          return (
            <article
              key={league.league_id}
              className={`commissioner-waivers-league-card ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleLeague(league.league_id)}
            >
              <div className="league-card-header">
                <label
                  className="league-checkbox-label"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleLeague(league.league_id)}
                  />
                  <strong className="league-name">{league.league_name}</strong>
                </label>

                <div className="league-meta-badges">
                  {(() => {
                    const match = getLeaguePresetMatch(
                      league,
                      inSeasonPreset?.sunday_to_saturday_settings || DEFAULT_STANDARD_PRESET,
                      offSeasonPreset?.sunday_to_saturday_settings || DEFAULT_OFFSEASON_PRESET,
                    );
                    if (!match) return null;
                    return (
                      <span
                        className={`preset-match-pill preset-${match.variant}`}
                        title={`League schedule matches ${match.label} preset`}
                      >
                        {match.label}
                      </span>
                    );
                  })()}
                  <span className={`status-pill ${league.daily_waivers ? 'active' : 'inactive'}`}>
                    {league.daily_waivers ? 'Daily Waivers ON' : 'Daily Waivers OFF'}
                  </span>
                  <span className="hour-pill">
                    {formatHour(league.daily_waivers_hour)}
                  </span>
                  <span className="hour-pill" title="After Games Waivers Clear">
                    After Games: {formatAfterGamesDay(league.waiver_day_of_week)}
                  </span>
                  <span className="hour-pill" title="Time on Waivers After Drop">
                    Drop Hold: {league.waiver_clear_days}d
                  </span>
                  <span className="roster-pill">
                    {league.total_rosters} Teams
                  </span>
                </div>
              </div>

              {/* Current League Schedule Preview */}
              <div className="league-schedule-preview">
                {league.schedule.map((item) => (
                  <div key={item.day} className="preview-day-item">
                    <span className="preview-day-label">{item.day.slice(0, 3)}</span>
                    <span className={`preview-day-badge ${getOptionBadgeClass(item.setting)}`}>
                      {getOptionLabel(item.setting)}
                    </span>
                  </div>
                ))}
              </div>
            </article>
          );
        })}

        {filteredLeagues.length === 0 && (
          <div className="commissioner-empty-state">
            No commissioner leagues found matching &quot;{search}&quot;.
          </div>
        )}
      </div>

      {/* Allow Custom Daily Waivers Info Modal */}
      {showInfoModal && (
        <div
          className="daily-waivers-modal-backdrop"
          onClick={() => setShowInfoModal(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="daily-waivers-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="daily-waivers-modal-header">
              <div className="daily-waivers-modal-title-group">
                <Info size={18} />
                <h4>Allow Custom Daily Waivers</h4>
              </div>
              <button
                type="button"
                className="daily-waivers-modal-close"
                onClick={() => setShowInfoModal(false)}
                aria-label="Close dialog"
              >
                <X size={16} />
              </button>
            </div>

            <div className="daily-waivers-modal-body">
              <div className="sleeper-quote-card">
                &ldquo;Specify custom times for waivers to clear. A player will clear only after passing all waiver settings checks, such as the &lsquo;After Games Waivers Clear&rsquo; setting.&rdquo;
              </div>

              <div className="info-content-section">
                <h5>How It Works</h5>
                <p>
                  Enabling <strong>Allow Custom Daily Waivers</strong> lets you define a specific transaction rule for every day of the week (Sunday through Saturday). Waiver requests will clear daily at your designated processing time.
                </p>
              </div>

              <div className="info-content-section">
                <h5>Daily Option Settings</h5>
                <ul className="info-waiver-types-list">
                  <li className="info-waiver-type-item">
                    <span className="type-badge badge-waivers">Waivers</span>
                    <div className="info-waiver-type-desc">
                      <strong>Waivers:</strong> Players remain on waivers all day and can only be acquired by submitting a waiver claim. Claims process at the daily processing time.
                    </div>
                  </li>
                  <li className="info-waiver-type-item">
                    <span className="type-badge badge-fa">Free Agent</span>
                    <div className="info-waiver-type-desc">
                      <strong>Free Agent (FA):</strong> Players can be picked up immediately on a first-come, first-served basis without waiting for waivers.
                    </div>
                  </li>
                  <li className="info-waiver-type-item">
                    <span className="type-badge badge-waiver-fa">Waivers → FA</span>
                    <div className="info-waiver-type-desc">
                      <strong>Waivers → Free Agent:</strong> Pending waiver claims process at the designated daily time, and any player not claimed immediately becomes an instant Free Agent for the rest of the day.
                    </div>
                  </li>
                  <li className="info-waiver-type-item">
                    <span className="type-badge badge-locked">Locked</span>
                    <div className="info-waiver-type-desc">
                      <strong>Locked:</strong> Player transactions (adds, drops, claims) are completely blocked for that day.
                    </div>
                  </li>
                </ul>
              </div>

              <div className="info-note-box">
                <div className="info-note-box-title">
                  <AlertTriangle size={15} style={{ flexShrink: 0 }} />
                  <span>Game Lock &amp; Clearance Checks</span>
                </div>
                <p>
                  <strong>Game Lock Rule:</strong> A player will only clear after passing all other waiver checks (such as the standard <em>After Games Waivers Clear</em> setting). Players whose games have started remain locked until their normal clearance day, regardless of whether a day is set to Free Agent.
                </p>
                <p style={{ marginTop: '8px' }}>
                  <strong>Thursday Game Example:</strong> If a player plays in a Thursday night game, and Sunday or Monday are set to <em>Waivers → FA</em> or <em>Free Agent</em>, that player will <strong>not</strong> become a Free Agent on Sunday. Because they have already played, they stay on waivers until Wednesday morning (or your league&apos;s configured <em>After Games Waivers Clear</em> day).
                </p>
                <p style={{ marginTop: '8px' }}>
                  <strong>Drop Hold Rule:</strong> Similarly, players who are dropped will stay on waivers for the number of days specified by your league&apos;s <em>Time on Waivers After Drop</em> setting (typically 2 days, or 0–3 days).
                </p>
              </div>
            </div>

            <div className="daily-waivers-modal-footer">
              <button
                type="button"
                className="button-primary"
                onClick={() => setShowInfoModal(false)}
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

