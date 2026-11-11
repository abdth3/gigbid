import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api/client';

const STAGES = ['drafted', 'submitted', 'viewed', 'replied', 'interview', 'hired', 'lost'];

export const PipelinePage: React.FC = () => {
  const [columns, setColumns] = useState<Record<string, any[]>>({});

  useEffect(() => {
    api.getPipeline().then((r) => setColumns(r.columns || {}));
  }, []);

  return (
    <div>
      <h2>Pipeline Board (Kanban)</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
        {STAGES.map((stage) => (
          <div key={stage} style={{ background: '#0f172a', borderRadius: 10, padding: 12, minHeight: 220 }}>
            <h4 style={{ marginTop: 0, textTransform: 'uppercase', fontSize: '0.8em', color: '#94a3b8' }}>
              {stage} ({(columns[stage] || []).length})
            </h4>
            <div style={{ display: 'grid', gap: 8 }}>
              {(columns[stage] || []).map((card) => (
                <Link
                  key={card.job_id}
                  to={`/studio/${card.job_id}`}
                  style={{ background: '#1e293b', padding: 10, borderRadius: 8, textDecoration: 'none', color: '#f8fafc', fontSize: '0.85em' }}
                >
                  <div style={{ fontWeight: 600 }}>{card.title}</div>
                  <div style={{ color: '#60a5fa', marginTop: 4 }}>${card.bid_amount_usd ?? '-'} · Fit {(card.fit_score * 100).toFixed(0)}%</div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
