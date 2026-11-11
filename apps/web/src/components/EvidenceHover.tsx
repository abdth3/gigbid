import React, { useState } from 'react';
import { EvidenceItem } from '../lib/api/client';

interface Props {
  text: string;
  evidence: EvidenceItem[];
}

export const EvidenceHover: React.FC<Props> = ({ text, evidence }) => {
  const [activeEv, setActiveEv] = useState<EvidenceItem | null>(null);
  const evMap = new Map(evidence.map((e) => [e.evidence_id, e]));

  const parts = text.split(/(\[[a-zA-Z0-9_-]+\])/g);

  return (
    <div style={{ position: 'relative', lineHeight: 1.7 }}>
      <p style={{ margin: 0 }}>
        {parts.map((part, idx) => {
          const m = part.match(/^\[([a-zA-Z0-9_-]+)\]$/);
          if (m) {
            const ev = evMap.get(m[1]);
            return (
              <span
                key={idx}
                onMouseEnter={() => ev && setActiveEv(ev)}
                onClick={() => ev && setActiveEv(ev)}
                style={{
                  background: ev ? '#1d4ed8' : '#991b1b',
                  color: '#fff',
                  padding: '2px 6px',
                  borderRadius: 4,
                  fontSize: '0.82em',
                  cursor: 'pointer',
                  margin: '0 2px',
                }}
                title={ev ? ev.title : 'Unverified citation'}
              >
                {part}
              </span>
            );
          }
          return <span key={idx}>{part}</span>;
        })}
      </p>

      {activeEv && (
        <div
          style={{
            marginTop: 10,
            padding: 12,
            background: '#0f172a',
            border: '1px solid #3b82f6',
            borderRadius: 8,
            fontSize: '0.88em',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <strong>{activeEv.title} ({activeEv.evidence_id})</strong>
            <button onClick={() => setActiveEv(null)} style={{ background: 'none', color: '#94a3b8', border: 'none', cursor: 'pointer' }}>
              Close
            </button>
          </div>
          <div style={{ color: '#cbd5e1' }}>{activeEv.summary}</div>
          <div style={{ color: '#60a5fa', marginTop: 4 }}>
            Outcome: {activeEv.outcome} · Source: {activeEv.source}
          </div>
        </div>
      )}
    </div>
  );
};
