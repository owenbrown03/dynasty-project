import { Routes, Route } from 'react-router';
import Home from './pages/home/Home';
import Trades from './pages/trades/Trades';
import Rosters from './pages/leagues/Rosters';

const AppRoutes = ({ handleUserSubmit, loading, username }) => {
  return (
    <Routes>
      <Route path="/" element={
        <Home 
          onSubmit={handleUserSubmit} 
          loading={loading}
        />
      } />
      <Route path="/trades" element={
        <Trades 
          username={username}
        />
      } />
      <Route path="/rosters" element={
        <Rosters 
          username={username}
        />
      } />
    </Routes>
  );
};

export default AppRoutes;