import React, { useEffect, useState } from 'react';
import { api } from '../lib/api/client';

export const MessagesPage: React.FC = () => {
  const [threads, setThreads] = useState<any[]>([]);
  const [drafted, setDrafted] = useState<Record<string, any>>({});
  const [status, setStatus] = useState('');

  const load = () => api.listMessages().then((r) => setThreads(r.threads || []));
  useEffect(() => { load(); }, []);

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <h2>Client Messages (Conversation Graph)</h2>
      {status && <div style={{ color: '#4ade80' }}>{status}</div>}
      {threads.length === 0 ? (
        <div style={{ color: '#94a3b8' }}>No client replies yet. Approve a high-fit proposal to receive a simulated client reply!</div>
      ) : (
        threads.map((t) => {
          const d = drafted[t.job_id];
          return (
            <div key={t.job_id} style={{ background: '#0f172a', padding: 14, borderRadius: 10 }}>
              <h4 style={{ marginTop: 0 }}>{t.job_title} ({t.job_id})</h4>
              <div style={{ display: 'grid', gap: 6, marginBottom: 10 }}>
                {t.messages.map((m: any) => (
                  <div key={m.message_id} style={{ background: m.sender === 'client' ? '#1e293b' : '#172554', padding: 8, borderRadius: 6 }}>
                    <strong>{m.sender}:</strong> {m.text}
                  </div>
                ))}
              </div>
              {!d ? (
                <button
                  onClick={async () => { const res = await api.draftReply(t.job_id); setDrafted({ ...drafted, [t.job_id]: res }); }}
                  style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '8px 12px', borderRadius: 6, cursor: 'pointer' }}
                >
                  Draft AI Reply & Interview Slots
                </button>
              ) : (
                <div style={{ background: '#1e293b', padding: 12, borderRadius: 8 }}>
                  <div><strong>Detected Intent:</strong> {d.client_intent?.intent}</div>
                  <p>{d.draft_reply}</p>
                  <button
                    onClick={async () => {
                      await api.approveReply({ job_id: t.job_id, action: 'approve' });
                      setStatus(`Reply sent for ${t.job_id} & interview hold created!`);
                      setDrafted({ ...drafted, [t.job_id]: null });
                      await load();
                    }}
                    style={{ background: '#16a34a', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: 6, cursor: 'pointer' }}
                  >
                    Approve & Send Reply
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
