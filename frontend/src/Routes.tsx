import { Routes, Route } from 'react-router';

import { Dashboard } from './pages/dashboard/Dashboard'; 
import { UsernameInput } from './pages/dashboard/UsernameInput';
import { Analytics } from './pages/dashboard/Analytics';
import { Trades } from './pages/trades/Trades';
import { Rosters } from './pages/leagues/Rosters';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<Dashboard />}>
        <Route path="/" element={<UsernameInput />} />
        <Route path="/dashboard/:username" element={<Analytics />} />
        <Route path="/trades/:username" element={<Trades />} />
        <Route path="/leagues/:username" element={<Rosters />} />
      </Route>
    </Routes>
  );
};