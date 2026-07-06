import { Routes, Route } from 'react-router';

import { DashboardLayout } from './components/layouts/DashboardLayout';
import { UsernameInput } from './pages/dashboard/UsernameInput';
import { LeagueDashboardPage } from './pages/dashboard/LeagueDashboardPage';
import { TradesPage } from './pages/trades/TradesPage';
import { LeaguesPage } from './pages/leagues/LeaguesPage';
import { WaiversPage } from './pages/waivers/WaiversPage';
import { OrphansPage } from './pages/orphans/OrphansPage';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<UsernameInput />} />
        <Route path="/dashboard" element={<LeagueDashboardPage />} />
        <Route path="/leagues" element={<LeaguesPage />} />
        <Route path="/trades" element={<TradesPage />} />
        <Route path="/waivers" element={<WaiversPage />} />
        <Route path="/orphans" element={<OrphansPage />} />
      </Route>
    </Routes>
  );
};