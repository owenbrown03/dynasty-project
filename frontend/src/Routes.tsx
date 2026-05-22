import { Routes, Route } from 'react-router';

import { DashboardLayout } from './components/layouts/DashboardLayout';
import { UsernameInput } from './pages/dashboard/UsernameInput';
import { Analytics } from './pages/dashboard/Analytics';
import { TradesPage } from './pages/trades/TradesPage';
import { RostersPage } from './pages/leagues/RostersPage';
import { OrphansPage } from './pages/orphans/OrphansPage';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<UsernameInput />} />
        <Route path="/dashboard" element={<Analytics />} />
        <Route path="/trades" element={<TradesPage />} />
        <Route path="/leagues" element={<RostersPage />} />
        <Route path="/orphans" element={<OrphansPage />} />
      </Route>
    </Routes>
  );
};