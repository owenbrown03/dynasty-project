import { Routes, Route } from 'react-router';
import Home from './pages/home/Home';
import Trades from './pages/trades/Trades';
import Rosters from './pages/leagues/Rosters';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/:routeUsername" element={<Home />} />
      <Route path="/trades" element={<Trades />} />
      <Route path="/rosters" element={<Rosters />} />
      <Route path="/:routeUsername/trades" element={<Trades />} />
      <Route path="/:routeUsername/rosters" element={<Rosters />} />
    </Routes>
  );
};

export default AppRoutes;
