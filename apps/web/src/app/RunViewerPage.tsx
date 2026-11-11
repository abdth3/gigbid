import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { RunTimeline } from '../components/RunTimeline';
import { api, RunRecord } from '../lib/api/client';

export const RunViewerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [selected, setSelected] = useState<RunRecord | null>(null);
  const [sseEvents, setSseEvents] = useState<string[]>([]);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    api.listRuns().then((r) => {
      const list = r.runs || [];
      setRuns(list);
      if (id) {
        setSelected(list.find((x: RunRecord) => x.job_id === id) || list[0] || null);
      } else {
        setSelected(list[0] || null);
      }
    });
    api.getMarketplaceStatus().then((s) => setOffline(s.offline));
  }, [id]);

  const startSseStream = (jobId: string) => {
    setSseEvents(['Connecting SSE stream...']);
    const es = new EventSource(`/api/runs/${jobId}/stream`);
    es.onmessage = (ev) => {
      setSseEvents((prev) => [...prev, ev.data]);
      const parsed = JSON.parse(ev.data);
      if (parsed.event === 'run_paused_or_finished') es.close();
    };
    es.onerror = () => es.close();
  };

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
        <h2 style={{ margin: 0 }}>Agent Run Viewer & Live SSE Stream</h2>
        <button
          onClick={async () => { const s = await api.setMarketplaceStatus(!offline); setOffline(s.offline); }}
          style={{ background: offline ? '#16a34a' : '#dc2626', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: 6, cursor: 'pointer' }}
        >
          {offline ? 'Restore Marketplace MCP Server' : 'Simulate Marketplace MCP Offline'}
        </button>
      </div>

      {selected ? (
        <div style={{ background: '#0f172a', padding: 16, borderRadius: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap' }}>
            <div>
              <strong>Job:</strong> {selected.job_id} · <strong>Thread:</strong> <code>{selected.thread_id}</code> · <strong>Trace:</strong> <code>{selected.trace_id}</code>
            </div>
            <button
              onClick={() => startSseStream(selected.job_id)}
              style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: 6, cursor: 'pointer' }}
            >
              Stream Live SSE Run
            </button>
          </div>
          <RunTimeline trace={selected.execution_trace || []} />
          {sseEvents.length > 0 && (
            <pre style={{ background: '#020617', padding: 10, borderRadius: 6, marginTop: 12, fontSize: '0.8em', overflowX: 'auto' }}>
              {sseEvents.join('\n')}
            </pre>
          )}
        </div>
      ) : (
        <div style={{ color: '#94a3b8' }}>No runs yet. Analyze a job from the Inbox to view its node-by-node trace.</div>
      )}
    </div>
  );
};
