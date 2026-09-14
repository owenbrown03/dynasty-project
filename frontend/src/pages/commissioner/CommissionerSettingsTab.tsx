import { useState, useMemo } from 'react';
import {
  AlertTriangle,
  ArrowLeftRight,
  Check,
  Filter,
  Info,
  Lock,
  Search,
  Shield,
  Trophy,
} from 'lucide-react';
import {
  useCommissionerSettingsOverview,
  useUpdateCommissionerSettings,
} from '@/hooks/sleeper/useUsers';
import { notify } from '@/utils/notify';
import { Skeleton } from '@/components/feedback/Skeleton';
import type {
  CommissionerSettingsUpdateRequest,
} from '@/api/v1/endpoints/sleeper/user.endpoints';

type LeagueTypeFilter = 'all' | 'best_ball' | 'lineup';

export const CommissionerSettingsTab = () => {
  const { data: leagues = [], isLoading, error } = useCommissionerSettingsOverview();
  const updateMutation = useUpdateCommissionerSettings();

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<LeagueTypeFilter>('all');
  const [selectedLeagues, setSelectedLeagues] = useState<Set<string>>(new Set());

  // Controls State ('keep' represents preserving each league's current value)
  const [benchLock, setBenchLock] = useState<number | 'keep'>('keep');
  const [disableAdds, setDisableAdds] = useState<number | 'keep'>('keep');
  const [offseasonAdds, setOffseasonAdds] = useState<number | 'keep'>('keep');

  const [disableTrades, setDisableTrades] = useState<number | 'keep'>('keep');
  const [tradeDeadline, setTradeDeadline] = useState<number | 'keep'>('keep');
  const [pickTrading, setPickTrading] = useState<number | 'keep'>('keep');
  const [tradeReviewDays, setTradeReviewDays] = useState<number | 'keep'>('keep');
  const [vetoAutoPoll, setVetoAutoPoll] = useState<number | 'keep'>('keep');

  const [leagueAverageMatch, setLeagueAverageMatch] = useState<number | 'keep'>('keep');
  const [playoffTeams, setPlayoffTeams] = useState<number | 'keep'>('keep');
  const [playoffWeekStart, setPlayoffWeekStart] = useState<number | 'keep'>('keep');

  const [waiverBidMin, setWaiverBidMin] = useState<number | 'keep'>('keep');

  const [taxiDeadline, setTaxiDeadline] = useState<number | 'keep'>('keep');
  const [taxiAllowVets, setTaxiAllowVets] = useState<number | 'keep'>('keep');
  const [taxiYears, setTaxiYears] = useState<number | 'keep'>('keep');

  const [reserveAllowOut, setReserveAllowOut] = useState<number | 'keep'>('keep');
  const [reserveAllowDoubtful, setReserveAllowDoubtful] = useState<number | 'keep'>('keep');
  const [reserveAllowSus, setReserveAllowSus] = useState<number | 'keep'>('keep');
  const [reserveAllowCov, setReserveAllowCov] = useState<number | 'keep'>('keep');
  const [reserveAllowNa, setReserveAllowNa] = useState<number | 'keep'>('keep');
  const [reserveAllowDnr, setReserveAllowDnr] = useState<number | 'keep'>('keep');

  // Filter leagues
  const filteredLeagues = useMemo(() => {
    return leagues.filter((league) => {
      const matchSearch = league.league_name.toLowerCase().includes(search.toLowerCase());
      const matchType =
        typeFilter === 'all'
          ? true
          : typeFilter === 'best_ball'
          ? league.best_ball === 1
          : league.best_ball === 0;
      return matchSearch && matchType;
    });
  }, [leagues, search, typeFilter]);

  const bestBallCount = useMemo(() => leagues.filter((l) => l.best_ball === 1).length, [leagues]);
  const lineupCount = useMemo(() => leagues.filter((l) => l.best_ball === 0).length, [leagues]);

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

  // Build list of active changes to display and confirm
  const pendingChanges = useMemo(() => {
    const list: { label: string; valueText: string }[] = [];

    if (benchLock !== 'keep') {
      list.push({
        label: 'Prevent Bench Drops After Kickoff',
        valueText: benchLock === 1 ? 'Prevent Drops (Locked)' : 'Allow Drops (Unlocked)',
      });
    }
    if (disableAdds !== 'keep') {
      list.push({
        label: 'Free Agent / Waiver Moves',
        valueText: disableAdds === 1 ? 'Locked (Adds Disabled)' : 'Allowed (Normal)',
      });
    }
    if (offseasonAdds !== 'keep') {
      list.push({
        label: 'Offseason Moves',
        valueText: offseasonAdds === 1 ? 'Allowed in Offseason' : 'Locked in Offseason',
      });
    }
    if (disableTrades !== 'keep') {
      list.push({
        label: 'Trading',
        valueText: disableTrades === 1 ? 'Disabled' : 'Enabled',
      });
    }
    if (tradeDeadline !== 'keep') {
      list.push({
        label: 'Trade Deadline',
        valueText: tradeDeadline === 99 ? 'No Deadline' : `Week ${tradeDeadline}`,
      });
    }
    if (pickTrading !== 'keep') {
      list.push({
        label: 'Draft Pick Trading',
        valueText: pickTrading === 1 ? 'Allowed' : 'Disabled',
      });
    }
    if (tradeReviewDays !== 'keep') {
      list.push({
        label: 'Trade Review Period',
        valueText: tradeReviewDays === 0 ? 'None (Instant)' : `${tradeReviewDays} Day(s)`,
      });
    }
    if (vetoAutoPoll !== 'keep') {
      list.push({
        label: 'Trade Veto Auto Poll',
        valueText: vetoAutoPoll === 1 ? 'Enabled' : 'Disabled',
      });
    }
    if (leagueAverageMatch !== 'keep') {
      list.push({
        label: 'Median / League Average Match',
        valueText: leagueAverageMatch === 1 ? 'Enabled (Extra Game)' : 'Disabled',
      });
    }
    if (playoffTeams !== 'keep') {
      list.push({
        label: 'Playoff Teams',
        valueText: `${playoffTeams} Teams`,
      });
    }
    if (playoffWeekStart !== 'keep') {
      list.push({
        label: 'Playoff Start Week',
        valueText: playoffWeekStart === 0 ? 'No Playoffs' : `Week ${playoffWeekStart}`,
      });
    }
    if (waiverBidMin !== 'keep') {
      list.push({
        label: 'Minimum FAAB Bid',
        valueText: `$${waiverBidMin}`,
      });
    }
    if (taxiDeadline !== 'keep') {
      list.push({
        label: 'Taxi Deadline',
        valueText: taxiDeadline === 0 ? 'No Deadline' : `Week ${taxiDeadline}`,
      });
    }
    if (taxiAllowVets !== 'keep') {
      list.push({
        label: 'Taxi Eligibility',
        valueText: taxiAllowVets === 1 ? 'Rookies & Vets' : 'Rookies Only',
      });
    }
    if (taxiYears !== 'keep') {
      list.push({
        label: 'Taxi Experience Limit',
        valueText: taxiYears === 0 ? 'Any / Unlimited' : `${taxiYears} Year(s)`,
      });
    }
    if (reserveAllowOut !== 'keep') {
      list.push({
        label: 'Allow Out on IR',
        valueText: reserveAllowOut === 1 ? 'Yes' : 'No',
      });
    }
    if (reserveAllowDoubtful !== 'keep') {
      list.push({
        label: 'Allow Doubtful on IR',
        valueText: reserveAllowDoubtful === 1 ? 'Yes' : 'No',
      });
    }
    if (reserveAllowSus !== 'keep') {
      list.push({
        label: 'Allow Suspended on IR',
        valueText: reserveAllowSus === 1 ? 'Yes' : 'No',
      });
    }
    if (reserveAllowCov !== 'keep') {
      list.push({
        label: 'Allow Covid on IR',
        valueText: reserveAllowCov === 1 ? 'Yes' : 'No',
      });
    }
    if (reserveAllowNa !== 'keep') {
      list.push({
        label: 'Allow Not Active on IR',
        valueText: reserveAllowNa === 1 ? 'Yes' : 'No',
      });
    }
    if (reserveAllowDnr !== 'keep') {
      list.push({
        label: 'Allow Did Not Report on IR',
        valueText: reserveAllowDnr === 1 ? 'Yes' : 'No',
      });
    }

    return list;
  }, [
    benchLock,
    disableAdds,
    offseasonAdds,
    disableTrades,
    tradeDeadline,
    pickTrading,
    tradeReviewDays,
    vetoAutoPoll,
    leagueAverageMatch,
    playoffTeams,
    playoffWeekStart,
    waiverBidMin,
    taxiDeadline,
    taxiAllowVets,
    taxiYears,
    reserveAllowOut,
    reserveAllowDoubtful,
    reserveAllowSus,
    reserveAllowCov,
    reserveAllowNa,
    reserveAllowDnr,
  ]);

  const handleApply = async () => {
    if (selectedLeagues.size === 0) return;

    if (pendingChanges.length === 0) {
      alert(
        'All settings are currently set to "Keep Current League Setting (Default)". Please select at least one setting change to apply.'
      );
      return;
    }

    const changesSummary = pendingChanges.map((c) => `• ${c.label}: ${c.valueText}`).join('\n');
    const confirmed = window.confirm(
      `Apply the following setting changes to ${selectedLeagues.size} selected league(s)?\n\n${changesSummary}`
    );
    if (!confirmed) return;

    const payload: CommissionerSettingsUpdateRequest = {
      league_ids: Array.from(selectedLeagues),
      bench_lock: benchLock === 'keep' ? null : benchLock,
      disable_adds: disableAdds === 'keep' ? null : disableAdds,
      offseason_adds: offseasonAdds === 'keep' ? null : offseasonAdds,
      disable_trades: disableTrades === 'keep' ? null : disableTrades,
      trade_deadline: tradeDeadline === 'keep' ? null : tradeDeadline,
      pick_trading: pickTrading === 'keep' ? null : pickTrading,
      trade_review_days: tradeReviewDays === 'keep' ? null : tradeReviewDays,
      veto_auto_poll: vetoAutoPoll === 'keep' ? null : vetoAutoPoll,
      league_average_match: leagueAverageMatch === 'keep' ? null : leagueAverageMatch,
      playoff_teams: playoffTeams === 'keep' ? null : playoffTeams,
      playoff_week_start: playoffWeekStart === 'keep' ? null : playoffWeekStart,
      waiver_bid_min: waiverBidMin === 'keep' ? null : waiverBidMin,
      taxi_deadline: taxiDeadline === 'keep' ? null : taxiDeadline,
      taxi_allow_vets: taxiAllowVets === 'keep' ? null : taxiAllowVets,
      taxi_years: taxiYears === 'keep' ? null : taxiYears,
      reserve_allow_out: reserveAllowOut === 'keep' ? null : reserveAllowOut,
      reserve_allow_doubtful: reserveAllowDoubtful === 'keep' ? null : reserveAllowDoubtful,
      reserve_allow_sus: reserveAllowSus === 'keep' ? null : reserveAllowSus,
      reserve_allow_cov: reserveAllowCov === 'keep' ? null : reserveAllowCov,
      reserve_allow_na: reserveAllowNa === 'keep' ? null : reserveAllowNa,
      reserve_allow_dnr: reserveAllowDnr === 'keep' ? null : reserveAllowDnr,
    };

    try {
      const res = await updateMutation.mutateAsync(payload);
      const failures = (res.results || []).filter((r) => !r.success);

      if (failures.length > 0) {
        const errorDetails = failures.map((f) => `${f.league_name}: ${f.error || 'Failed'}`).join('; ');
        notify.error(`Updated with some errors: ${errorDetails}`);
      } else {
        notify.success(`Successfully updated settings for ${res.successful_leagues} league(s)!`);
        setSelectedLeagues(new Set());
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update league settings';
      notify.error(msg);
    }
  };

  const handleResetControls = () => {
    setBenchLock('keep');
    setDisableAdds('keep');
    setOffseasonAdds('keep');
    setDisableTrades('keep');
    setTradeDeadline('keep');
    setPickTrading('keep');
    setTradeReviewDays('keep');
    setVetoAutoPoll('keep');
    setLeagueAverageMatch('keep');
    setPlayoffTeams('keep');
    setPlayoffWeekStart('keep');
    setWaiverBidMin('keep');
    setTaxiDeadline('keep');
    setTaxiAllowVets('keep');
    setTaxiYears('keep');
    setReserveAllowOut('keep');
    setReserveAllowDoubtful('keep');
    setReserveAllowSus('keep');
    setReserveAllowCov('keep');
    setReserveAllowNa('keep');
    setReserveAllowDnr('keep');
  };

  if (isLoading) {
    return (
      <div className="commissioner-settings-tab">
        <Skeleton width="100%" height={260} />
        <div style={{ marginTop: '24px' }}>
          <Skeleton width="100%" height={320} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="commissioner-error-card">
        <AlertTriangle size={20} />
        <div>
          <h4>Failed to load commissioner leagues</h4>
          <p>{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="commissioner-settings-tab">
      {/* Top Configuration Card */}
      <section className="commissioner-settings-config-card">
        <div className="config-header">
          <div>
            <div className="config-title-row">
              <h3 className="config-title">Bulk League Settings</h3>
            </div>
            <p className="config-subtitle">
              Batch update general league settings across selected commissioner leagues. Any setting left as &ldquo;Keep Current League Setting&rdquo; will remain unchanged.
            </p>
          </div>
          <div className="config-actions">
            <button
              type="button"
              className="button-secondary btn-sm"
              onClick={handleResetControls}
              disabled={pendingChanges.length === 0}
              title="Reset all dropdowns back to Keep Current League Setting"
            >
              Reset Controls
            </button>
            <button
              type="button"
              className="button-primary"
              disabled={selectedLeagues.size === 0 || updateMutation.isPending}
              onClick={handleApply}
            >
              {updateMutation.isPending
                ? 'Applying Settings...'
                : `Apply to ${selectedLeagues.size} Selected League${selectedLeagues.size === 1 ? '' : 's'}`}
            </button>
          </div>
        </div>

        {/* Best Ball Bench Lock Callout */}
        <div className="best-ball-notice-box">
          <div className="best-ball-notice-title">
            <Info size={15} style={{ flexShrink: 0 }} />
            <span>Best Ball &amp; Bench Lock Shortcut</span>
          </div>
          <p>
            In Sleeper Best Ball leagues, Sleeper&apos;s UI hides the <em>&ldquo;Prevent bench players from being dropped after game starts&rdquo;</em> option. This page writes directly to Sleeper&apos;s API, enabling you to turn on Bench Lock for your Best Ball leagues without having to temporarily switch them to Lineup mode.
          </p>
        </div>

        {/* Controls Sections */}
        <div className="settings-groups-container">
          {/* Group: Roster & Drops */}
          <div className="settings-group-card">
            <div className="settings-group-title">
              <Lock size={15} />
              <span>Roster &amp; Drop Rules</span>
            </div>
            <div className="settings-group-fields">
              <div className="control-group">
                <span className="control-label">Bench Drop Lock</span>
                <select
                  value={benchLock}
                  onChange={(e) => setBenchLock(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="1">Prevent Bench Drops (Locked)</option>
                  <option value="0">Allow Bench Drops (Unlocked)</option>
                </select>
                <span className="control-hint">Prevent bench player drops after kickoff</span>
              </div>

              <div className="control-group">
                <span className="control-label">Free Agent / Waiver Moves</span>
                <select
                  value={disableAdds}
                  onChange={(e) => setDisableAdds(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="0">Allowed (Normal)</option>
                  <option value="1">Locked (Disable All Moves)</option>
                </select>
                <span className="control-hint">Lock all player adds across the league</span>
              </div>

              <div className="control-group">
                <span className="control-label">Offseason Moves</span>
                <select
                  value={offseasonAdds}
                  onChange={(e) => setOffseasonAdds(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="1">Allowed in Offseason</option>
                  <option value="0">Locked in Offseason</option>
                </select>
                <span className="control-hint">Allow player moves before season starts</span>
              </div>
            </div>
          </div>

          {/* Group: Trading */}
          <div className="settings-group-card">
            <div className="settings-group-title">
              <ArrowLeftRight size={15} />
              <span>Trading</span>
            </div>
            <div className="settings-group-fields">
              <div className="control-group">
                <span className="control-label">Trading Access</span>
                <select
                  value={disableTrades}
                  onChange={(e) => setDisableTrades(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="0">Trading Allowed</option>
                  <option value="1">Trading Disabled</option>
                </select>
                <span className="control-hint">Allow player &amp; pick trades</span>
              </div>

              <div className="control-group">
                <span className="control-label">Trade Deadline</span>
                <select
                  value={tradeDeadline}
                  onChange={(e) => setTradeDeadline(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="99">No Deadline</option>
                  <option value="9">Week 9</option>
                  <option value="10">Week 10</option>
                  <option value="11">Week 11 (Standard)</option>
                  <option value="12">Week 12</option>
                  <option value="13">Week 13</option>
                  <option value="14">Week 14</option>
                </select>
                <span className="control-hint">Final week trades can be proposed</span>
              </div>

              <div className="control-group">
                <span className="control-label">Draft Pick Trading</span>
                <select
                  value={pickTrading}
                  onChange={(e) => setPickTrading(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="1">Enabled</option>
                  <option value="0">Disabled</option>
                </select>
                <span className="control-hint">Allow future draft picks in trades</span>
              </div>

              <div className="control-group">
                <span className="control-label">Trade Review Period</span>
                <select
                  value={tradeReviewDays}
                  onChange={(e) => setTradeReviewDays(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="0">None (Instant)</option>
                  <option value="1">1 Day</option>
                  <option value="2">2 Days</option>
                  <option value="3">3 Days</option>
                </select>
                <span className="control-hint">Review window before processing</span>
              </div>

              <div className="control-group">
                <span className="control-label">Trade Veto Auto Poll</span>
                <select
                  value={vetoAutoPoll}
                  onChange={(e) => setVetoAutoPoll(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="0">Disabled (Commissioner / Instant)</option>
                  <option value="1">Enabled (League Veto Poll)</option>
                </select>
                <span className="control-hint">Automatically create veto voting poll</span>
              </div>
            </div>
          </div>

          {/* Group: Matchups & Playoffs */}
          <div className="settings-group-card">
            <div className="settings-group-title">
              <Trophy size={15} />
              <span>Matchups &amp; Playoffs</span>
            </div>
            <div className="settings-group-fields">
              <div className="control-group">
                <span className="control-label">Median Match (League Avg)</span>
                <select
                  value={leagueAverageMatch}
                  onChange={(e) => setLeagueAverageMatch(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="1">Enabled (Extra Game vs Median)</option>
                  <option value="0">Disabled</option>
                </select>
                <span className="control-hint">Extra weekly match against league median</span>
              </div>

              <div className="control-group">
                <span className="control-label">Playoff Teams</span>
                <select
                  value={playoffTeams}
                  onChange={(e) => setPlayoffTeams(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="4">4 Teams</option>
                  <option value="5">5 Teams</option>
                  <option value="6">6 Teams (Standard)</option>
                  <option value="7">7 Teams</option>
                  <option value="8">8 Teams</option>
                </select>
                <span className="control-hint">Number of teams qualifying for playoffs</span>
              </div>

              <div className="control-group">
                <span className="control-label">Playoff Start Week</span>
                <select
                  value={playoffWeekStart}
                  onChange={(e) => setPlayoffWeekStart(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="14">Week 14</option>
                  <option value="15">Week 15 (Standard)</option>
                  <option value="16">Week 16</option>
                  <option value="0">No Playoffs</option>
                </select>
                <span className="control-hint">Week when postseason rounds begin</span>
              </div>

              <div className="control-group">
                <span className="control-label">Minimum FAAB Bid</span>
                <select
                  value={waiverBidMin}
                  onChange={(e) => setWaiverBidMin(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="0">$0 Min Bid</option>
                  <option value="1">$1 Min Bid</option>
                </select>
                <span className="control-hint">Minimum waiver claim dollar amount</span>
              </div>
            </div>
          </div>

          {/* Group: Taxi & IR */}
          <div className="settings-group-card">
            <div className="settings-group-title">
              <Shield size={15} />
              <span>Taxi Squad &amp; Reserve (IR)</span>
            </div>
            <div className="settings-group-fields">
              <div className="control-group">
                <span className="control-label">Taxi Deadline</span>
                <select
                  value={taxiDeadline}
                  onChange={(e) => setTaxiDeadline(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="0">No Deadline</option>
                  <option value="1">Week 1 (Start of Season)</option>
                  <option value="2">Week 2</option>
                  <option value="3">Week 3</option>
                  <option value="4">Week 4</option>
                </select>
                <span className="control-hint">When taxi squad slots lock</span>
              </div>

              <div className="control-group">
                <span className="control-label">Taxi Allow Veterans</span>
                <select
                  value={taxiAllowVets}
                  onChange={(e) => setTaxiAllowVets(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="0">Rookies Only</option>
                  <option value="1">Rookies &amp; Veterans</option>
                </select>
                <span className="control-hint">Allow non-rookies on taxi squads</span>
              </div>

              <div className="control-group">
                <span className="control-label">Taxi Experience Limit</span>
                <select
                  value={taxiYears}
                  onChange={(e) => setTaxiYears(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="0">Any / Unlimited</option>
                  <option value="1">1 Year Max</option>
                  <option value="2">2 Years Max</option>
                  <option value="3">3 Years Max</option>
                  <option value="4">4 Years Max</option>
                </select>
                <span className="control-hint">Maximum NFL seasons for taxi players</span>
              </div>

              <div className="control-group">
                <span className="control-label">Allow Out on IR</span>
                <select
                  value={reserveAllowOut}
                  onChange={(e) => setReserveAllowOut(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="1">Yes (Allowed)</option>
                  <option value="0">No</option>
                </select>
                <span className="control-hint">Players designated Out can go on IR</span>
              </div>

              <div className="control-group">
                <span className="control-label">Allow Doubtful on IR</span>
                <select
                  value={reserveAllowDoubtful}
                  onChange={(e) => setReserveAllowDoubtful(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="1">Yes (Allowed)</option>
                  <option value="0">No</option>
                </select>
                <span className="control-hint">Players designated Doubtful can go on IR</span>
              </div>

              <div className="control-group">
                <span className="control-label">Allow Suspended on IR</span>
                <select
                  value={reserveAllowSus}
                  onChange={(e) => setReserveAllowSus(e.target.value === 'keep' ? 'keep' : Number(e.target.value))}
                  className="hour-select"
                >
                  <option value="keep">Keep Current League Setting (Default)</option>
                  <option value="1">Yes (Allowed)</option>
                  <option value="0">No</option>
                </select>
                <span className="control-hint">Suspended players can go on IR</span>
              </div>
            </div>
          </div>
        </div>

        {/* Pending Changes Summary Banner */}
        {pendingChanges.length > 0 && (
          <div className="settings-pending-summary-bar">
            <div className="settings-pending-summary-title">
              <Check size={14} />
              <span>{pendingChanges.length} Setting{pendingChanges.length === 1 ? '' : 's'} to update:</span>
            </div>
            <div className="settings-pending-pills">
              {pendingChanges.map((c) => (
                <span key={c.label} className="settings-pending-pill">
                  <strong>{c.label}:</strong> {c.valueText}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Leagues List Section */}
      <section className="commissioner-waivers-leagues-section">
        <div className="leagues-toolbar">
          <div className="toolbar-search-group">
            <div className="search-input-wrapper">
              <Search size={15} className="search-icon" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search commissioner leagues..."
                className="search-input"
              />
            </div>

            {/* Type Filter Pills */}
            <div className="type-filter-pills">
              <button
                type="button"
                className={`type-pill ${typeFilter === 'all' ? 'active' : ''}`}
                onClick={() => setTypeFilter('all')}
              >
                All ({leagues.length})
              </button>
              <button
                type="button"
                className={`type-pill ${typeFilter === 'best_ball' ? 'active' : ''}`}
                onClick={() => setTypeFilter('best_ball')}
              >
                Best Ball ({bestBallCount})
              </button>
              <button
                type="button"
                className={`type-pill ${typeFilter === 'lineup' ? 'active' : ''}`}
                onClick={() => setTypeFilter('lineup')}
              >
                Lineup ({lineupCount})
              </button>
            </div>
          </div>

          <div className="toolbar-selection-group">
            <span className="selected-count-badge">
              {selectedLeagues.size} of {filteredLeagues.length} Selected
            </span>
            <button type="button" className="button-secondary btn-sm" onClick={handleSelectAll}>
              Select All
            </button>
            <button
              type="button"
              className="button-secondary btn-sm"
              onClick={handleSelectNone}
              disabled={selectedLeagues.size === 0}
            >
              Select None
            </button>
          </div>
        </div>

        {filteredLeagues.length === 0 ? (
          <div className="leagues-empty-state">
            <Filter size={24} />
            <p>No commissioner leagues match your search or filter.</p>
          </div>
        ) : (
          <div className="leagues-card-grid">
            {filteredLeagues.map((league) => {
              const isSelected = selectedLeagues.has(league.league_id);
              return (
                <div
                  key={league.league_id}
                  className={`waiver-league-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => toggleLeague(league.league_id)}
                >
                  <div className="league-card-header-row">
                    <div className="league-card-title-group">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleLeague(league.league_id)}
                        onClick={(e) => e.stopPropagation()}
                        aria-label={`Select ${league.league_name}`}
                      />
                      <span className="league-name">{league.league_name}</span>
                    </div>
                    <span className="league-roster-count">{league.total_rosters} Teams</span>
                  </div>

                  <div className="league-card-meta-row">
                    {league.best_ball === 1 ? (
                      <span className="league-status-badge badge-best-ball">Best Ball</span>
                    ) : (
                      <span className="league-status-badge badge-lineup">Lineup</span>
                    )}

                    <span
                      className={`league-status-badge ${
                        league.bench_lock === 1 ? 'badge-bench-locked' : 'badge-bench-unlocked'
                      }`}
                    >
                      Bench Lock: {league.bench_lock === 1 ? 'ON' : 'OFF'}
                    </span>

                    <span className="league-status-badge badge-secondary-meta">
                      Deadline: {league.trade_deadline === 99 ? 'None' : `Wk ${league.trade_deadline}`}
                    </span>

                    <span
                      className={`league-status-badge ${
                        league.disable_trades === 1 ? 'badge-trades-disabled' : 'badge-trades-enabled'
                      }`}
                    >
                      Trades: {league.disable_trades === 1 ? 'OFF' : 'ON'}
                    </span>

                    <span className="league-status-badge badge-secondary-meta">
                      Playoffs: {league.playoff_teams}t (Wk {league.playoff_week_start})
                    </span>

                    {league.league_average_match === 1 && (
                      <span className="league-status-badge badge-secondary-meta">Median Match</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
};
