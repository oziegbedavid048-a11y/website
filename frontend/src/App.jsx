import { useEffect } from 'react';
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import CookieBanner from './components/CookieBanner.jsx';
import Home from './pages/Home.jsx';
import SignIn from './pages/SignIn.jsx';
import SignUp from './pages/SignUp.jsx';
import ForgotPassword from './pages/ForgotPassword.jsx';
import Terminal from './pages/Terminal.jsx';
import { VerifyPage } from './pages/Verify.jsx';
import {
  AccountHome, TradeHistoryPage,
} from './pages/AccountPages.jsx';
import { DepositPage, WithdrawPage } from './pages/Funding.jsx';
import { SupportPage } from './pages/Support.jsx';
import { setChatBubble } from './lib/livechat.js';
import { LegalRoute, NotFound, PricingPage } from './pages/InfoPages.jsx';
import {
  AboutPage, AccountsPage, ArticlePage, HelpPage, LearnPage, MarketsPage, PlatformPage, ServicesPage,
} from './pages/SitePages.jsx';

/** Scrolls to #hash targets (smoothly) or to the top on page change. */
function ScrollManager() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) {
      const id = decodeURIComponent(hash.slice(1));
      let tries = 0;
      const attempt = () => {
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        else if (tries++ < 10) setTimeout(attempt, 60);
      };
      attempt();
    } else {
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  }, [pathname, hash]);
  return null;
}

function SiteLayout() {
  // Public pages show the live chat bubble.
  useEffect(() => { setChatBubble(true); }, []);
  return (
    <>
      <a href="#main" className="skip-link">Skip to main content</a>
      <Header />
      <Outlet />
      <Footer />
    </>
  );
}

/** Shown only on the static preview build, where the backend is not running. */
function PreviewNotice() {
  if (!import.meta.env.VITE_STATIC_PREVIEW) return null;
  return (
    <p className="preview-notice" role="note">
      Website preview. Signing in, the dashboard and live prices need the server, which is not running here.
    </p>
  );
}

export default function App() {
  return (
    <>
      <PreviewNotice />
      <ScrollManager />
      <CookieBanner />
      <Routes>
        <Route element={<SiteLayout />}>
          <Route index element={<Home />} />
          <Route path="pricing" element={<PricingPage />} />
          <Route path="platform" element={<PlatformPage />} />
          <Route path="markets" element={<MarketsPage />} />
          <Route path="accounts" element={<AccountsPage />} />
          <Route path="learn" element={<LearnPage />} />
          <Route path="services" element={<ServicesPage />} />
          <Route path="help" element={<HelpPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="insights/:slug" element={<ArticlePage />} />
          <Route path="legal/:slug" element={<LegalRoute />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        {/* Focused flows without the marketing header, like the real broker sites. */}
        <Route path="sign-in" element={<SignIn />} />
        <Route path="sign-up" element={<SignUp />} />
        <Route path="forgot-password" element={<ForgotPassword />} />

        {/* Signed-in client area */}
        <Route path="account" element={<AccountHome />} />
        <Route path="account/terminal" element={<Terminal />} />
        <Route path="account/deposit" element={<DepositPage />} />
        <Route path="account/withdraw" element={<WithdrawPage />} />
        <Route path="account/verify" element={<VerifyPage />} />
        <Route path="account/support" element={<SupportPage />} />
        <Route path="account/history" element={<TradeHistoryPage />} />
        <Route path="account/funding-history" element={<Navigate to="/account/deposit" replace />} />
        <Route path="dashboard" element={<Navigate to="/account" replace />} />
      </Routes>
    </>
  );
}
