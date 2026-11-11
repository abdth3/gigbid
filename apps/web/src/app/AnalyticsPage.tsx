import React, { useEffect, useState } from 'react';
import { api } from '../lib/api/client';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.getAnalytics().then(setData);
  }, []);

  if (!data) return <div>Loading analytics...</div>;
  const live = data.live_metrics || {};

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <h2>Analytics & Evaluation Metrics</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
        <StatCard label="Jobs Analyzed" value={live.total_jobs_analyzed} />
        <StatCard label="Proposals Submitted" value={live.proposals_submitted} />
        <StatCard label="Client Replies" value={live.client_replies} />
        <StatCard label="Reply Rate" value={`${((live.reply_rate || 0) * 100).toFixed(1)}%`} />
        <StatCard label="Connects Spent" value={live.connects_spent} />
        <StatCard label="Connects Balance" value={live.connects_balance} />
      </div>

      <div style={{ background: '#0f172a', padding: 16, borderRadius: 10 }}>
        <h3 style={{ marginTop: 0 }}>Committed Benchmark Results (evals/results/)</h3>
        <pre style={{ fontSize: '0.82em', overflowX: 'auto', color: '#cbd5e1' }}>
          {JSON.stringify(data.eval_results, null, 2)}
        </pre>
      </div>
    </div>
  );
};

const StatCard: React.FC<{ label: string; value: any }> = ({ label, value }) => (
  <div style={{ background: '#0f172a', padding: 14, borderRadius: 10, border: '1px solid #1e293b' }}>
    <div style={{ fontSize: '0.82em', color: '#94a3b8' }}>{label}</div>
    <div style={{ fontSize: '1.5em', fontWeight: 700, marginTop: 4 }}>{value}</div>
  </div>
);
