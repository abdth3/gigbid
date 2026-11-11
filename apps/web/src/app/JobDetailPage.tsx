import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, RunRecord } from '../lib/api/client';

export const JobDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<{ job: any; run: RunRecord | null; stage: string } | null>(null);

  useEffect(() => {
    if (id) api.getJobDetail(id).then(setData);
  }, [id]);

  if (!data) return <div>Loading job detail...</div>;
  const { job, run } = data;

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
        <h2 style={{ margin: 0 }}>{job.title}</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {!run && (
            <button
              onClick={async () => { await api.analyzeJob(job.job_id); api.getJobDetail(job.job_id).then(setData); }}
              style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: 6, cursor: 'pointer' }}
            >
              Run Multi-Agent Analysis
            </button>
          )}
          {run && (
            <Link to={`/studio/${job.job_id}`} style={{ background: '#16a34a', color: '#fff', padding: '8px 14px', borderRadius: 6, textDecoration: 'none' }}>
              Open Proposal Studio
            </Link>
          )}
        </div>
      </div>

      <div style={{ background: '#0f172a', padding: 14, borderRadius: 10 }}>
        <strong>Description:</strong>
        <p style={{ color: '#cbd5e1' }}>{job.description}</p>
      </div>

      {run && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
            <div style={{ background: '#0f172a', padding: 14, borderRadius: 10 }}>
              <h4 style={{ marginTop: 0 }}>Decision & Price Rationale</h4>
              <p>Action: <strong>{run.decision?.action?.toUpperCase()}</strong></p>
              <p style={{ color: '#94a3b8' }}>{run.decision?.reason}</p>
              {run.price_quote && <p style={{ color: '#60a5fa' }}>{run.price_quote.rationale}</p>}
            </div>
            <div style={{ background: '#0f172a', padding: 14, borderRadius: 10 }}>
              <h4 style={{ marginTop: 0 }}>Risk Report</h4>
              <p>Score: <strong>{run.risk_report?.score}</strong> · Scam: {String(run.risk_report?.is_scam)}</p>
              <p style={{ color: '#94a3b8' }}>{run.risk_report?.explanation}</p>
            </div>
          </div>

          <div style={{ background: '#0f172a', padding: 14, borderRadius: 10 }}>
            <h4 style={{ marginTop: 0 }}>Requirement-to-Evidence Matrix</h4>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9em' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid #334155' }}>
                  <th style={{ padding: 8 }}>Requirement</th>
                  <th style={{ padding: 8 }}>Portfolio Evidence ID</th>
                  <th style={{ padding: 8 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {(run.fit_report?.requirement_matrix || []).map((row: any, i: number) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: 8 }}>{row.requirement}</td>
                    <td style={{ padding: 8 }}><code>{row.evidence_id}</code></td>
                    <td style={{ padding: 8 }}>{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};
