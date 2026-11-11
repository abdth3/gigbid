import React, { useState } from 'react';
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import { AnalyticsPage } from './app/AnalyticsPage';
import { InboxPage } from './app/InboxPage';
import { JobDetailPage } from './app/JobDetailPage';
import { MessagesPage } from './app/MessagesPage';
import { OnboardingPage } from './app/OnboardingPage';
import { PipelinePage } from './app/PipelinePage';
import { RunViewerPage } from './app/RunViewerPage';
import { SettingsPage } from './app/SettingsPage';
import { StudioPage } from './app/StudioPage';

export function App() {
  const [tick, setTick] = useState(0);

  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', background: '#020617', color: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
        <header style={{ borderBottom: '1px solid #1e293b', padding: '12px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <Link to="/inbox" style={{ fontWeight: 800, fontSize: '1.2em', color: '#60a5fa', textDecoration: 'none' }}>
            GigBid Copilot
          </Link>
          <nav style={{ display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: '0.92em' }}>
            <Link to="/" style={navLink}>Onboarding</Link>
            <Link to="/inbox" style={navLink}>Inbox</Link>
            <Link to="/pipeline" style={navLink}>Pipeline</Link>
            <Link to="/messages" style={navLink}>Messages</Link>
            <Link to="/runs" style={navLink}>Agent Runs</Link>
            <Link to="/analytics" style={navLink}>Analytics</Link>
            <Link to="/settings" style={navLink}>Settings</Link>
          </nav>
        </header>
        <main style={{ maxWidth: 1150, margin: '0 auto', padding: '20px 16px' }}>
          <Routes>
            <Route path="/" element={<OnboardingPage onDone={() => setTick(tick + 1)} />} />
            <Route path="/inbox" element={<InboxPage />} />
            <Route path="/jobs/:id" element={<JobDetailPage />} />
            <Route path="/studio/:id" element={<StudioPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/messages" element={<MessagesPage />} />
            <Route path="/runs" element={<RunViewerPage />} />
            <Route path="/runs/:id" element={<RunViewerPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

const navLink: React.CSSProperties = {
  color: '#cbd5e1',
  textDecoration: 'none',
  fontWeight: 500,
};

export default App;
