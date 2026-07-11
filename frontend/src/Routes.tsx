import { Navigate, Routes, Route } from 'react-router';

import { DashboardLayout } from './components/layouts/DashboardLayout';
import { UsernameInput } from './pages/dashboard/UsernameInput';
import { LeagueDashboardPage } from './pages/dashboard/LeagueDashboardPage';
import { TradesPage } from './pages/trades/TradesPage';
import { LeaguesPage } from './pages/leagues/LeaguesPage';
import { WaiversPage } from './pages/waivers/WaiversPage';
import { TiersPage } from './pages/tiers/TiersPage';
import { CommissionerPage } from './pages/commissioner/CommissionerPage';

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
        <Route path="/commissioner" element={<CommissionerPage />} />
        <Route path="/commissioner/:username" element={<CommissionerPage />} />
        <Route path="/orphans" element={<CommissionerPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
};
