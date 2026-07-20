import { Suspense, lazy, type ReactNode } from 'react';
import { Navigate, Routes, Route } from 'react-router';

import { LoadingState } from '@/components/feedback/LoadingState';
import { DashboardLayout } from './components/layouts/DashboardLayout';

const LeagueDashboardPage = lazy(async () => ({
  default: (await import('./pages/dashboard/LeagueDashboardPage')).LeagueDashboardPage,
}));
const TradesPage = lazy(async () => ({
  default: (await import('./pages/trades/TradesPage')).TradesPage,
}));
const LeaguesPage = lazy(async () => ({
  default: (await import('./pages/leagues/LeaguesPage')).LeaguesPage,
}));
const WaiversPage = lazy(async () => ({
  default: (await import('./pages/waivers/WaiversPage')).WaiversPage,
}));
const TiersPage = lazy(async () => ({
  default: (await import('./pages/tiers/TiersPage')).TiersPage,
}));
const CommissionerPage = lazy(async () => ({
  default: (await import('./pages/commissioner/CommissionerPage')).CommissionerPage,
}));
const FinancePage = lazy(async () => ({
  default: (await import('./pages/finance/FinancePage')).FinancePage,
}));
const MyValuesPage = lazy(async () => ({
  default: (await import('./pages/my-values/MyValuesPage')).MyValuesPage,
}));
const RemindersPage = lazy(async () => ({
  default: (await import('./pages/reminders/RemindersPage')).RemindersPage,
}));
const AuctionDraftPage = lazy(async () => ({
  default: (await import('./pages/auction/AuctionDraftPage')).AuctionDraftPage,
}));
const AdpPage = lazy(async () => ({
  default: (await import('./pages/adp/AdpPage')).AdpPage,
}));

function withPageFallback(
  element: ReactNode,
) {
  return (
    <Suspense fallback={<LoadingState label="Loading page..." />}>
      {element}
    </Suspense>
  );
}

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={withPageFallback(<LeagueDashboardPage />)} />
        <Route path="/leagues" element={withPageFallback(<LeaguesPage />)} />
        <Route path="/trades" element={withPageFallback(<TradesPage />)} />
        <Route path="/waivers" element={withPageFallback(<WaiversPage />)} />
        <Route path="/tiers" element={withPageFallback(<TiersPage />)} />
        <Route path="/adp" element={withPageFallback(<AdpPage />)} />
        <Route path="/my-values" element={withPageFallback(<MyValuesPage />)} />
        <Route path="/finance" element={withPageFallback(<FinancePage />)} />
        <Route path="/reminders" element={withPageFallback(<RemindersPage />)} />
        <Route path="/auction" element={withPageFallback(<AuctionDraftPage />)} />
        <Route path="/commissioner" element={withPageFallback(<CommissionerPage />)} />
        <Route path="/commissioner/:username" element={withPageFallback(<CommissionerPage />)} />
        <Route path="/orphans" element={withPageFallback(<CommissionerPage />)} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
};
