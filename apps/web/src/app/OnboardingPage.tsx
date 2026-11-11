import React, { useEffect, useState } from 'react';
import { api } from '../lib/api/client';

export const OnboardingPage: React.FC<{ onDone: () => void }> = ({ onDone }) => {
  const [username, setUsername] = useState('reviewer');
  const [password, setPassword] = useState('gigbid-reviewer-2026');
  const [persona, setPersona] = useState('ai_ml_engineer');
  const [rate, setRate] = useState(55);
  const [budget, setBudget] = useState(60);
  const [mode, setMode] = useState('gigsim');
  const [portfolioTitle, setPortfolioTitle] = useState('');
  const [portfolioSummary, setPortfolioSummary] = useState('');
  const [portfolioItems, setPortfolioItems] = useState<any[]>([]);
  const [status, setStatus] = useState('');

  const loadPortfolio = async () => {
    const res = await api.listPortfolio();
    setPortfolioItems(res.items || []);
  };

  useEffect(() => {
    loadPortfolio();
  }, []);

  const handleLoginAndSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const loginRes = await api.login(username, password);
      localStorage.setItem('gigbid_token', loginRes.token);
      await api.onboard({ persona, hourly_rate_usd: rate, weekly_connects_budget: budget, marketplace_mode: mode });
      setStatus('Signed in and profile configured!');
      await loadPortfolio();
      onDone();
    } catch (err: any) {
      setStatus(err.message || 'Login failed');
    }
  };

  const handleUpload = async () => {
    if (!portfolioTitle || !portfolioSummary) return;
    await api.uploadPortfolio({
      title: portfolioTitle,
      summary: portfolioSummary,
      skills: ['Python', 'LangGraph'],
      industry: 'SaaS',
      outcome: 'Delivered in production',
    });
    setPortfolioTitle('');
    setPortfolioSummary('');
    await loadPortfolio();
  };

  return (
    <div style={{ display: 'grid', gap: 20, maxWidth: 850 }}>
      <h2>Sign-in & Onboarding</h2>
      <form onSubmit={handleLoginAndSave} style={{ display: 'grid', gap: 12, background: '#0f172a', padding: 16, borderRadius: 10 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} style={inputStyle} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={inputStyle} />
          </label>
          <label>
            Persona Profile
            <select value={persona} onChange={(e) => setPersona(e.target.value)} style={inputStyle}>
              <option value="ai_ml_engineer">AI/ML Engineer</option>
              <option value="fullstack_web_dev">Full-Stack Web Dev</option>
              <option value="data_analyst">Data Analyst</option>
            </select>
          </label>
          <label>
            Marketplace Mode
            <select value={mode} onChange={(e) => setMode(e.target.value)} style={inputStyle}>
              <option value="gigsim">GigSim Simulator</option>
              <option value="upwork_live">Upwork Official MCP (OAuth)</option>
            </select>
          </label>
          <label>
            Hourly Rate (USD)
            <input type="number" value={rate} onChange={(e) => setRate(Number(e.target.value))} style={inputStyle} />
          </label>
          <label>
            Weekly Connects Budget
            <input type="number" value={budget} onChange={(e) => setBudget(Number(e.target.value))} style={inputStyle} />
          </label>
        </div>
        <button type="submit" style={btnPrimary}>Sign In & Save Profile</button>
        {status && <div style={{ color: '#4ade80' }}>{status}</div>}
      </form>

      <div style={{ background: '#0f172a', padding: 16, borderRadius: 10 }}>
        <h3 style={{ marginTop: 0 }}>Portfolio Corpus ({portfolioItems.length} indexed items)</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
          <input placeholder="New case study title" value={portfolioTitle} onChange={(e) => setPortfolioTitle(e.target.value)} style={inputStyle} />
          <input placeholder="Outcome & summary" value={portfolioSummary} onChange={(e) => setPortfolioSummary(e.target.value)} style={{ ...inputStyle, flex: 1 }} />
          <button type="button" onClick={handleUpload} style={btnPrimary}>Add & Re-index</button>
        </div>
        <div style={{ maxHeight: 220, overflowY: 'auto', display: 'grid', gap: 6 }}>
          {portfolioItems.slice(0, 12).map((it) => (
            <div key={it.evidence_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: '#1e293b', borderRadius: 6, fontSize: '0.85em' }}>
              <span><strong>{it.evidence_id}</strong> — {it.title}</span>
              <button
                onClick={async () => { await api.deletePortfolio(it.evidence_id); await loadPortfolio(); }}
                style={{ background: '#7f1d1d', color: '#fff', border: 'none', borderRadius: 4, padding: '2px 8px', cursor: 'pointer' }}
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const inputStyle: React.CSSProperties = {
  display: 'block',
  width: '100%',
  marginTop: 4,
  padding: '8px 10px',
  background: '#1e293b',
  color: '#f8fafc',
  border: '1px solid #334155',
  borderRadius: 6,
};

const btnPrimary: React.CSSProperties = {
  background: '#2563eb',
  color: '#fff',
  border: 'none',
  padding: '10px 16px',
  borderRadius: 6,
  cursor: 'pointer',
  fontWeight: 600,
};
