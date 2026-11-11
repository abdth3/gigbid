import React, { useEffect, useState } from 'react';
import { api } from '../lib/api/client';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [msg, setMsg] = useState('');

  const load = () => api.getSettings().then(setSettings);
  useEffect(() => { load(); }, []);

  if (!settings) return <div>Loading settings...</div>;

  return (
    <div style={{ display: 'grid', gap: 16, maxWidth: 800 }}>
      <h2>Settings & Long-Term Memory Viewer</h2>
      {msg && <div style={{ color: '#4ade80' }}>{msg}</div>}

      <div style={{ background: '#0f172a', padding: 16, borderRadius: 10, display: 'grid', gap: 8 }}>
        <div><strong>Autonomy Level:</strong> {settings.autonomy_level} (Never auto-sends!)</div>
        <div><strong>Marketplace Mode:</strong> <code>{settings.marketplace_mode}</code></div>
        <div><strong>Active RAG Variant:</strong> <code>{settings.rag_variant}</code></div>
        <div><strong>Weekly Connects Budget:</strong> {settings.weekly_connects_budget}</div>
      </div>

      <div style={{ background: '#0f172a', padding: 16, borderRadius: 10 }}>
        <h3 style={{ marginTop: 0 }}>Style Memory (Promoted from User Edit Diffs)</h3>
        {(settings.memory?.style_memory || []).map((m: any) => (
          <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', padding: 8, background: '#1e293b', borderRadius: 6, marginBottom: 6 }}>
            <span>{m.rule} <small style={{ color: '#94a3b8' }}>({m.source})</small></span>
            <button
              onClick={async () => { await api.deleteMemory('style_memory', m.id); setMsg(`Deleted ${m.id}`); await load(); }}
              style={{ background: '#7f1d1d', color: '#fff', border: 'none', borderRadius: 4, padding: '4px 10px', cursor: 'pointer' }}
            >
              Delete
            </button>
          </div>
        ))}

        <h3>Outcome Memory (Promoted from Won/Replied Proposals)</h3>
        {(settings.memory?.outcome_memory || []).length === 0 ? (
          <div style={{ color: '#94a3b8' }}>No outcome memories promoted yet.</div>
        ) : (
          settings.memory.outcome_memory.map((m: any) => (
            <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', padding: 8, background: '#1e293b', borderRadius: 6, marginBottom: 6 }}>
              <span>{m.rule}</span>
              <button
                onClick={async () => { await api.deleteMemory('outcome_memory', m.id); setMsg(`Deleted ${m.id}`); await load(); }}
                style={{ background: '#7f1d1d', color: '#fff', border: 'none', borderRadius: 4, padding: '4px 10px', cursor: 'pointer' }}
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
