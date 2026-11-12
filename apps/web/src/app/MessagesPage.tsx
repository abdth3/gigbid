import React, { useEffect, useState } from 'react';
import { api } from '../lib/api/client';

export const MessagesPage: React.FC = () => {
  const [threads, setThreads] = useState<any[]>([]);
  const [drafted, setDrafted] = useState<Record<string, any>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [status, setStatus] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const load = () => api.listMessages().then((r) => setThreads(r.threads || []));
  useEffect(() => { load(); }, []);

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <h2>Client Messages (Conversation Graph)</h2>
      {status && <div style={{ color: '#4ade80' }}>{status}</div>}
      {errorMsg && <div role="alert" style={{ background: '#7f1d1d', padding: 10, borderRadius: 8 }}>{errorMsg}</div>}
      {threads.length === 0 ? (
        <div style={{ color: '#94a3b8' }}>No client replies yet. Approve a high-fit proposal in Studio to receive a simulated client reply!</div>
      ) : (
        threads.map((t) => {
          const d = drafted[t.job_id];
          return (
            <div key={t.job_id} className="gb-card">
              <h4 style={{ marginTop: 0 }}>{t.job_title} ({t.job_id})</h4>
              <div style={{ display: 'grid', gap: 6, marginBottom: 12 }}>
                {t.messages.map((m: any) => (
                  <div key={m.message_id} style={{ background: m.sender === 'client' ? '#1e293b' : '#172554', padding: 10, borderRadius: 8 }}>
                    <strong>{m.sender}:</strong> {m.text}
                  </div>
                ))}
              </div>
              {!d ? (
                <button
                  disabled={busyId === t.job_id}
                  onClick={async () => {
                    try {
                      setBusyId(t.job_id);
                      setErrorMsg('');
                      const res = await api.draftReply(t.job_id);
                      if (res.detail) throw new Error(res.detail);
                      setDrafted({ ...drafted, [t.job_id]: res });
                    } catch (err: any) {
                      setErrorMsg(err?.message || 'Failed to draft reply');
                    } finally {
                      setBusyId(null);
                    }
                  }}
                  style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: 6, cursor: 'pointer' }}
                >
                  {busyId === t.job_id ? 'Drafting Reply & Slots...' : 'Draft AI Reply & Interview Slots'}
                </button>
              ) : (
                <div style={{ background: '#1e293b', padding: 14, borderRadius: 8 }}>
                  <div><strong>Detected Intent:</strong> <code>{d.client_intent?.intent || 'interview_request'}</code></div>
                  <p>{d.draft_reply}</p>
                  {d.proposed_slots?.length > 0 && (
                    <div style={{ fontSize: '0.85em', color: '#60a5fa', marginBottom: 10 }}>
                      Proposed Slots: {d.proposed_slots.map((s: any) => s.label).join(' · ')}
                    </div>
                  )}
                  <button
                    disabled={busyId === t.job_id}
                    onClick={async () => {
                      try {
                        setBusyId(t.job_id);
                        await api.approveReply({ job_id: t.job_id, action: 'approve' });
                        setStatus(`Reply sent for ${t.job_id} & interview hold created!`);
                        setDrafted({ ...drafted, [t.job_id]: null });
                        await load();
                      } finally {
                        setBusyId(null);
                      }
                    }}
                    style={{ background: '#16a34a', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: 6, cursor: 'pointer' }}
                  >
                    {busyId === t.job_id ? 'Sending...' : 'Approve & Send Reply'}
                  </button>
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
};
