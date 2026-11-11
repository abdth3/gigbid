import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApprovalPanel } from '../components/ApprovalPanel';
import { EvidenceHover } from '../components/EvidenceHover';
import { api, RunRecord } from '../lib/api/client';

export const StudioPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<RunRecord | null>(null);
  const [msg, setMsg] = useState('');

  const load = async () => {
    if (!id) return;
    const res = await api.getJobDetail(id);
    setRun(res.run);
  };

  useEffect(() => {
    load();
  }, [id]);

  if (!run) return <div>No proposal run found for this job. <Link to="/inbox">Back to Inbox</Link></div>;

  const draft = run.proposal_draft || {};
  const lastCritique = run.critiques?.[run.critiques.length - 1];
  const compliance = run.compliance_verdict;

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0 }}>Proposal Studio — {run.job_id}</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={async () => { const r = await api.regenerateProposal(run.job_id); setRun(r.run); setMsg('Regenerated & re-verified against current portfolio.'); }}
            style={{ background: '#475569', color: '#fff', border: 'none', padding: '8px 12px', borderRadius: 6, cursor: 'pointer' }}
          >
            Regenerate & Re-verify
          </button>
          <Link to={`/runs/${run.job_id}`} style={{ background: '#1e293b', color: '#60a5fa', padding: '8px 12px', borderRadius: 6, textDecoration: 'none' }}>
            View Agent Trace
          </Link>
        </div>
      </div>

      {msg && <div style={{ color: '#4ade80' }}>{msg}</div>}

      <div style={{ background: '#0f172a', padding: 16, borderRadius: 10 }}>
        <h4 style={{ marginTop: 0 }}>Evidence-Grounded Draft (Hover or click any [evidence_id] badge)</h4>
        <EvidenceHover text={draft.cover_letter || ''} evidence={run.evidence || []} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
        <div style={{ background: '#0f172a', padding: 12, borderRadius: 8 }}>
          <strong>Claim Verification:</strong>{' '}
          Unsupported before: {run.claim_verification?.unsupported_before ?? 0} → after: {run.claim_verification?.unsupported_after ?? 0}
        </div>
        <div style={{ background: '#0f172a', padding: 12, borderRadius: 8 }}>
          <strong>Critic:</strong> {lastCritique ? (lastCritique.passed ? 'Passed' : lastCritique.issues.join(', ')) : 'Passed'}
        </div>
        <div style={{ background: '#0f172a', padding: 12, borderRadius: 8 }}>
          <strong>Compliance Guard:</strong> {compliance?.passed ? 'Passed' : `Blocked: ${compliance?.blocked_reasons?.join(', ')}`}
        </div>
      </div>

      <ApprovalPanel
        run={run}
        onApprove={async () => { const r = await api.approveProposal(run.job_id, { action: 'approve' }); setRun(r.run); setMsg('Approved & submitted!'); }}
        onEdit={async (edited) => { const r = await api.approveProposal(run.job_id, { action: 'edit', edited_cover_letter: edited }); setRun(r.run); setMsg('Edited, promoted to Style Memory, & submitted!'); }}
        onReject={async (reason) => { const r = await api.approveProposal(run.job_id, { action: 'reject', reason }); setRun(r.run); setMsg('Rejected with reason.'); }}
      />
    </div>
  );
};
