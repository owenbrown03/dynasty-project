import { Routes, Route } from 'react-router';
import Home from './pages/home/Home';
import Trades from './pages/trades/Trades';
import Leagues from './pages/leagues/Leagues';

const AppRoutes = ({ handleUserSubmit, transactions, loading, username }) => (
  <Routes>
    <Route path="/" element={
      <Home 
        onSubmit={handleUserSubmit} 
        loading={loading}
      />
    } />
    <Route path="/trades" element={
      <Trades 
        transactions={transactions}
        username={username}
        loading={loading}
      />
    } />
    <Route path="/leagues" element={<Leagues />} />
  </Routes>
);

export default AppRoutes;