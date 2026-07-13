import { Navigate, Routes, Route } from 'react-router';

import { DashboardLayout } from './components/layouts/DashboardLayout';
import { UsernameInput } from './pages/dashboard/UsernameInput';
import { LeagueDashboardPage } from './pages/dashboard/LeagueDashboardPage';
import { TradesPage } from './pages/trades/TradesPage';
import { LeaguesPage } from './pages/leagues/LeaguesPage';
import { WaiversPage } from './pages/waivers/WaiversPage';
import { TiersPage } from './pages/tiers/TiersPage';
import { CommissionerPage } from './pages/commissioner/CommissionerPage';
import { FinancePage } from './pages/finance/FinancePage';
import { MyValuesPage } from './pages/my-values/MyValuesPage';
import { RemindersPage } from './pages/reminders/RemindersPage';
import { SettingsPage } from './pages/settings/SettingsPage';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<UsernameInput />} />
        <Route path="/dashboard" element={<LeagueDashboardPage />} />
        <Route path="/leagues" element={<LeaguesPage />} />
        <Route path="/trades" element={<TradesPage />} />
        <Route path="/waivers" element={<WaiversPage />} />
        <Route path="/tiers" element={<TiersPage />} />
        <Route path="/my-values" element={<MyValuesPage />} />
        <Route path="/finance" element={<FinancePage />} />
        <Route path="/reminders" element={<RemindersPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/commissioner" element={<CommissionerPage />} />
        <Route path="/commissioner/:username" element={<CommissionerPage />} />
        <Route path="/orphans" element={<CommissionerPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
};
