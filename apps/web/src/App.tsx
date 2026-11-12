import React, { useState } from 'react';
import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router-dom';
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
      <div style={{ minHeight: '100vh', color: '#f8fafc' }}>
        <header
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 20,
            backdropFilter: 'blur(12px)',
            background: 'rgba(3, 7, 18, 0.85)',
            borderBottom: '1px solid #1e293b',
            padding: '12px 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Link to="/inbox" style={{ fontWeight: 800, fontSize: '1.22em', color: '#60a5fa', textDecoration: 'none' }}>
              ⚡ GigBid Copilot
            </Link>
            <span
              style={{
                fontSize: '0.75em',
                background: 'rgba(22, 163, 74, 0.16)',
                color: '#4ade80',
                border: '1px solid rgba(22, 163, 74, 0.35)',
                padding: '2px 8px',
                borderRadius: 999,
              }}
            >
              Open Profile · Groq gpt-oss
            </span>
          </div>
          <nav style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <NavLink to="/" end className={({ isActive }) => `gb-nav-link ${isActive ? 'active' : ''}`}>Onboarding</NavLink>
            <NavLink to="/inbox" className={({ isActive }) => `gb-nav-link ${isActive ? 'active' : ''}`}>Inbox</NavLink>
            <NavLink to="/pipeline" className={({ isActive }) => `gb-nav-link ${isActive ? 'active' : ''}`}>Pipeline</NavLink>
            <NavLink to="/messages" className={({ isActive }) => `gb-nav-link ${isActive ? 'active' : ''}`}>Messages</NavLink>
            <NavLink to="/runs" className={({ isActive }) => `gb-nav-link ${isActive ? 'active' : ''}`}>Agent Runs</NavLink>
            <NavLink to="/analytics" className={({ isActive }) => `gb-nav-link ${isActive ? 'active' : ''}`}>Analytics</NavLink>
            <NavLink to="/settings" className={({ isActive }) => `gb-nav-link ${isActive ? 'active' : ''}`}>Settings</NavLink>
          </nav>
        </header>
        <main style={{ maxWidth: 1180, margin: '0 auto', padding: '24px 18px' }}>
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

export default App;
