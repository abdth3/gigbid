import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, JobItem } from '../lib/api/client';

export const InboxPage: React.FC = () => {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [query, setQuery] = useState('');
  const [degraded, setDegraded] = useState(false);
  const [banner, setBanner] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = async (q = query) => {
    try {
      setErrorMsg('');
      const res = await api.listJobs(q);
      setDegraded(res.degraded);
      setBanner(res.banner || '');
      setJobs(res.jobs || []);
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to load jobs. Please sign in again on Onboarding.');
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleAnalyze = async (jobId: string) => {
    try {
      setBusyId(jobId);
      setErrorMsg('');
      const res = await api.analyzeJob(jobId);
      if (res.degraded) {
        setDegraded(true);
        setBanner(res.message);
      }
      await load();
    } catch (err: any) {
      setErrorMsg(err?.message || 'Analysis failed.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <h2>Job Inbox</h2>
      {errorMsg && (
        <div role="alert" style={{ background: '#7f1d1d', border: '1px solid #ef4444', padding: 12, borderRadius: 8, marginBottom: 14 }}>
          {errorMsg}
        </div>
      )}
      {degraded && (
        <div role="alert" style={{ background: '#7f1d1d', border: '1px solid #ef4444', padding: 12, borderRadius: 8, marginBottom: 14 }}>
          <strong>Degraded Mode:</strong> {banner || 'Marketplace unavailable. Work is queued.'}
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          placeholder="Filter jobs by skill or title..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ flex: 1, padding: 8, background: '#1e293b', color: '#fff', border: '1px solid #334155', borderRadius: 6 }}
        />
        <button onClick={() => load(query)} style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: 6, cursor: 'pointer' }}>
          Search
        </button>
      </div>

      {jobs.length === 0 ? (
        <div style={{ color: '#94a3b8' }}>No jobs visible right now.</div>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {jobs.slice(0, 25).map((j) => (
            <div key={j.job_id} style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 10, padding: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
                <div>
                  <Link to={`/jobs/${j.job_id}`} style={{ color: '#60a5fa', fontWeight: 600, fontSize: '1.05em', textDecoration: 'none' }}>
                    {j.title}
                  </Link>
                  <div style={{ fontSize: '0.85em', color: '#94a3b8', marginTop: 4 }}>
                    Budget: ${j.budget?.min ?? 0}–${j.budget?.max ?? 0} · Connects: {j.connects_cost} · Skills: {j.required_skills.join(', ')}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ background: '#1e293b', padding: '4px 8px', borderRadius: 6, fontSize: '0.82em' }}>
                    {j.recommended_action === 'pending' ? 'Fit: Not analyzed' : `Fit: ${(j.fit_score * 100).toFixed(0)}%`}
                  </span>
                  <span style={{ background: j.is_scam || j.risk_score > 0.5 ? '#7f1d1d' : (j.recommended_action === 'pending' ? '#1e293b' : '#14532d'), padding: '4px 8px', borderRadius: 6, fontSize: '0.82em' }}>
                    {j.recommended_action === 'pending' ? 'Risk: Pending' : (j.is_scam ? 'SCAM RISK' : `Risk: ${j.risk_score}`)}
                  </span>
                  <span style={{ background: '#334155', padding: '4px 8px', borderRadius: 6, fontSize: '0.82em' }}>
                    {j.recommended_action.toUpperCase()}
                  </span>
                  <button
                    disabled={busyId === j.job_id}
                    onClick={() => handleAnalyze(j.job_id)}
                    style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: 6, cursor: 'pointer' }}
                  >
                    {busyId === j.job_id ? 'Running...' : 'Analyze & Draft'}
                  </button>
                  {j.thread_id && (
                    <Link to={`/studio/${j.job_id}`} style={{ background: '#16a34a', color: '#fff', padding: '6px 12px', borderRadius: 6, textDecoration: 'none', fontSize: '0.85em' }}>
                      Open Studio
                    </Link>
                  )}
                  <button
                    onClick={async () => { await api.skipJob(j.job_id); await load(); }}
                    style={{ background: '#475569', color: '#fff', border: 'none', padding: '6px 10px', borderRadius: 6, cursor: 'pointer' }}
                  >
                    Skip
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
