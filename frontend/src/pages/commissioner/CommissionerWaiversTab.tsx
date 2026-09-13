import { useState, useMemo } from 'react';
import {
  useCommissionerWaiversOverview,
  useUpdateCommissionerWaivers,
} from '@/hooks/sleeper/useUsers';
import { notify } from '@/utils/notify';
import { Skeleton } from '@/components/feedback/Skeleton';

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

function formatHour(hour: number): string {
  const match = HOURS_OF_DAY.find((h) => h.value === hour);
  return match ? match.label : `${hour}:00`;
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

  const [search, setSearch] = useState('');
  const [selectedLeagues, setSelectedLeagues] = useState<Set<string>>(new Set());

  // Configuration state
  const [dailyWaiversEnabled, setDailyWaiversEnabled] = useState(true);
  const [processingHour, setProcessingHour] = useState<number | 'keep'>('keep');

  // Sunday to Saturday schedule (indices 0..6: Sun, Mon, Tue, Wed, Thu, Fri, Sat)
  // Default: All Waivers (1)
  const [schedule, setSchedule] = useState<number[]>([1, 1, 1, 1, 1, 1, 1]);

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
    setSchedule((prev) => {
      const next = [...prev];
      next[dayIndex] = value;
      return next;
    });
  };

  // Presets
  const applyPreset = (presetSchedule: number[]) => {
    setSchedule(presetSchedule);
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
            <h3 className="config-title">Custom Waivers Schedule</h3>
            <p className="config-subtitle">
              Configure daily waiver behavior across Sunday through Saturday.
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
                : `Apply to ${selectedLeagues.size} Selected League${selectedLeagues.size === 1 ? '' : 's'}`}
            </button>
          </div>
        </div>

        {/* Global toggles: Enabled + Processing Hour */}
        <div className="config-row-controls">
          <div className="control-group">
            <span className="control-label">Daily Waivers</span>
            <div className="toggle-pill-group">
              <button
                type="button"
                className={`toggle-pill ${dailyWaiversEnabled ? 'active' : ''}`}
                onClick={() => setDailyWaiversEnabled(true)}
              >
                Enabled
              </button>
              <button
                type="button"
                className={`toggle-pill ${!dailyWaiversEnabled ? 'active' : ''}`}
                onClick={() => setDailyWaiversEnabled(false)}
              >
                Disabled
              </button>
            </div>
          </div>

          <div className="control-group">
            <span className="control-label">Daily Waivers Processing Time</span>
            <select
              value={processingHour}
              onChange={(e) => {
                const val = e.target.value;
                setProcessingHour(val === 'keep' ? 'keep' : Number(val));
              }}
              className="hour-select"
            >
              <option value="keep">Keep Current League Setting</option>
              {HOURS_OF_DAY.map((h) => (
                <option key={h.value} value={h.value}>
                  {h.label}
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
                onClick={() => applyPreset([0, 2, 2, 1, 0, 0, 0])}
                title="Wed Waivers, Mon/Tue Locked, Thu/Fri/Sat/Sun FA"
              >
                Standard In-Season
              </button>
              <button
                type="button"
                className="button-secondary btn-sm"
                onClick={() => applyPreset([2, 2, 2, 2, 2, 2, 2])}
                title="All days locked"
              >
                Lock All
              </button>
            </div>
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
                  <span className={`status-pill ${league.daily_waivers ? 'active' : 'inactive'}`}>
                    {league.daily_waivers ? 'Daily Waivers ON' : 'Daily Waivers OFF'}
                  </span>
                  <span className="hour-pill">
                    {formatHour(league.daily_waivers_hour)}
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
            No commissioner leagues found matching "{search}".
          </div>
        )}
      </div>
    </div>
  );
};
