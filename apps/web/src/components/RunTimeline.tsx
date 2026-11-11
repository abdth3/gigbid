import React from 'react';

interface TraceItem {
  node: string;
  tool: string;
  model: string;
  tokens: number;
  cost_usd: number;
  latency_ms: number;
  observation: string;
  trace_id: string;
}

export const RunTimeline: React.FC<{ trace: TraceItem[] }> = ({ trace }) => {
  if (!trace || trace.length === 0) {
    return <div style={{ color: '#94a3b8' }}>No execution trace recorded yet.</div>;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {trace.map((t, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '10px 12px',
            background: '#1e293b',
            borderRadius: 8,
            borderLeft: '4px solid #3b82f6',
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          <div>
            <strong style={{ color: '#60a5fa' }}>{t.node}</strong>{' '}
            <span style={{ color: '#94a3b8', fontSize: '0.85em' }}>({t.model} · tool: {t.tool})</span>
            <div style={{ fontSize: '0.88em', color: '#e2e8f0', marginTop: 2 }}>{t.observation}</div>
          </div>
          <div style={{ fontSize: '0.8em', color: '#94a3b8', textAlign: 'right' }}>
            <div>{t.tokens} tok · {t.latency_ms}ms</div>
            <div>${t.cost_usd.toFixed(5)}</div>
          </div>
        </div>
      ))}
    </div>
  );
};
