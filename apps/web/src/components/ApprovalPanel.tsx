import React, { useState } from 'react';
import { RunRecord } from '../lib/api/client';

interface Props {
  run: RunRecord;
  onApprove: () => Promise<void>;
  onEdit: (editedText: string) => Promise<void>;
  onReject: (reason: string) => Promise<void>;
}

export const ApprovalPanel: React.FC<Props> = ({ run, onApprove, onEdit, onReject }) => {
  const draft = run.proposal_draft || {};
  const price = run.price_quote || {};
  const [editedText, setEditedText] = useState(draft.cover_letter || '');
  const [rejectReason, setRejectReason] = useState('');
  const [busy, setBusy] = useState(false);

  const isPending = run.approval_status === 'pending_approval';

  return (
    <div style={{ border: '1px solid #334155', borderRadius: 10, padding: 16, background: '#0f172a' }}>
      <h3 style={{ marginTop: 0 }}>Human Approval Gate (LangGraph Interrupt)</h3>
      <div style={{ fontSize: '0.9em', color: '#94a3b8', marginBottom: 12 }}>
        <strong>Dry-Run Preview:</strong> Bid ${price.bid_amount_usd ?? '-'} USD · Connects Cost: {price.connects_cost ?? '-'} · Status: <code>{run.approval_status}</code>
      </div>

      <label style={{ display: 'block', marginBottom: 6, fontSize: '0.85em', color: '#cbd5e1' }}>
        Edit Cover Letter (edits are diffed into Style Memory & re-checked):
      </label>
      <textarea
        aria-label="Edit Cover Letter"
        rows={5}
        value={editedText}
        onChange={(e) => setEditedText(e.target.value)}
        style={{
          width: '100%',
          background: '#1e293b',
          color: '#f8fafc',
          border: '1px solid #475569',
          borderRadius: 6,
          padding: 10,
          marginBottom: 10,
        }}
      />

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <button
          disabled={!isPending || busy}
          onClick={async () => { setBusy(true); await onApprove(); setBusy(false); }}
          style={{ background: '#16a34a', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 6, cursor: 'pointer' }}
        >
          Approve & Submit Draft
        </button>
        <button
          disabled={!isPending || busy}
          onClick={async () => { setBusy(true); await onEdit(editedText); setBusy(false); }}
          style={{ background: '#2563eb', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 6, cursor: 'pointer' }}
        >
          Save Edit & Approve
        </button>
        <input
          placeholder="Rejection reason..."
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          style={{ background: '#1e293b', color: '#fff', border: '1px solid #475569', borderRadius: 6, padding: '8px 10px' }}
        />
        <button
          disabled={!isPending || busy}
          onClick={async () => { setBusy(true); await onReject(rejectReason || 'Not a fit'); setBusy(false); }}
          style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 6, cursor: 'pointer' }}
        >
          Reject
        </button>
      </div>
    </div>
  );
};
