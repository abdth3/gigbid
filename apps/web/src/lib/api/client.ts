// Generated from FastAPI OpenAPI schema (/openapi.json) — do not hand-edit
export interface JobItem {
  job_id: string;
  title: string;
  description: string;
  required_skills: string[];
  budget: { min?: number; max?: number; currency?: string };
  connects_cost: number;
  fit_score: number;
  risk_score: number;
  is_scam: boolean;
  recommended_action: string;
  stage: string;
  thread_id?: string | null;
  approval_status?: string | null;
}

export interface EvidenceItem {
  evidence_id: string;
  type: string;
  title: string;
  summary: string;
  skills: string[];
  date: string;
  client_industry: string;
  outcome: string;
  source: string;
  score: number;
}

export interface RunRecord {
  thread_id: string;
  trace_id: string;
  job_id: string;
  job_spec?: any;
  risk_report?: any;
  fit_report?: any;
  evidence: EvidenceItem[];
  decision?: { action: string; reason: string };
  price_quote?: any;
  proposal_draft?: any;
  claim_verification?: any;
  critiques: any[];
  compliance_verdict?: any;
  execution_trace: any[];
  tokens_used: number;
  approval_status: string;
  submission_result?: any;
}

const BASE = '';

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('gigbid_token') || 'demo-reviewer-token';
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

export const api = {
  async login(username: string, password: string) {
    const r = await fetch(`${BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!r.ok) throw new Error('Invalid login credentials');
    return r.json();
  },
  async me() {
    const r = await fetch(`${BASE}/api/auth/me`, { headers: authHeaders() });
    return r.json();
  },
  async onboard(payload: any) {
    const r = await fetch(`${BASE}/api/auth/onboarding`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    return r.json();
  },
  async listPortfolio() {
    const r = await fetch(`${BASE}/api/auth/portfolio`, { headers: authHeaders() });
    return r.json();
  },
  async uploadPortfolio(payload: any) {
    const r = await fetch(`${BASE}/api/auth/portfolio`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    return r.json();
  },
  async deletePortfolio(evidenceId: string) {
    const r = await fetch(`${BASE}/api/auth/portfolio/${evidenceId}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    return r.json();
  },
  async listJobs(query = ''): Promise<{ degraded: boolean; banner?: string; jobs: JobItem[] }> {
    const r = await fetch(`${BASE}/api/jobs?query=${encodeURIComponent(query)}`, { headers: authHeaders() });
    return r.json();
  },
  async getJobDetail(jobId: string): Promise<{ job: any; run: RunRecord | null; stage: string }> {
    const r = await fetch(`${BASE}/api/jobs/${jobId}`, { headers: authHeaders() });
    return r.json();
  },
  async analyzeJob(jobId: string, strategy = 'evidence_first') {
    const r = await fetch(`${BASE}/api/jobs/analyze`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ job_id: jobId, strategy }),
    });
    return r.json();
  },
  async skipJob(jobId: string, reason = 'Skipped by user') {
    const r = await fetch(`${BASE}/api/jobs/${jobId}/skip?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return r.json();
  },
  async approveProposal(jobId: string, payload: { action: string; edited_cover_letter?: string; reason?: string }) {
    const r = await fetch(`${BASE}/api/proposals/${jobId}/approve`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    return r.json();
  },
  async regenerateProposal(jobId: string) {
    const r = await fetch(`${BASE}/api/proposals/${jobId}/regenerate`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ paragraph_index: 0, instruction: 'Re-verify against current portfolio' }),
    });
    return r.json();
  },
  async getPipeline() {
    const r = await fetch(`${BASE}/api/proposals/pipeline`, { headers: authHeaders() });
    return r.json();
  },
  async listMessages() {
    const r = await fetch(`${BASE}/api/messages`, { headers: authHeaders() });
    return r.json();
  },
  async draftReply(jobId: string) {
    const r = await fetch(`${BASE}/api/messages/${jobId}/draft`, { method: 'POST', headers: authHeaders() });
    return r.json();
  },
  async approveReply(payload: { job_id: string; action: string; edited_reply?: string }) {
    const r = await fetch(`${BASE}/api/messages/approve`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    return r.json();
  },
  async listRuns() {
    const r = await fetch(`${BASE}/api/runs`, { headers: authHeaders() });
    return r.json();
  },
  async getMarketplaceStatus() {
    const r = await fetch(`${BASE}/api/runs/marketplace-status`, { headers: authHeaders() });
    return r.json();
  },
  async setMarketplaceStatus(offline: boolean) {
    const r = await fetch(`${BASE}/api/runs/marketplace-status?offline=${offline}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    return r.json();
  },
  async getAnalytics() {
    const r = await fetch(`${BASE}/api/analytics`, { headers: authHeaders() });
    return r.json();
  },
  async getSettings() {
    const r = await fetch(`${BASE}/api/settings`, { headers: authHeaders() });
    return r.json();
  },
  async updateSettings(payload: any) {
    const r = await fetch(`${BASE}/api/settings`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    return r.json();
  },
  async deleteMemory(memoryType: string, itemId: string) {
    const r = await fetch(`${BASE}/api/settings/memory/${memoryType}/${itemId}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    return r.json();
  },
};
