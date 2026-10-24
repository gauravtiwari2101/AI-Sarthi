// API service layer — all backend communication
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Types
export interface District {
  id: number;
  name: string;
  aliases: string[];
  division: string;
  region: string;
  population_lakh: number | null;
  vulnerability_index: number | null;
}

export interface FinancialRecord {
  id: number;
  district_name: string | null;
  financial_year: string;
  programme: string | null;
  scheme: string | null;
  pool: string | null;
  financial_stage: string;
  amount_lakh: number;
  scope: string;
  source_document: string | null;
  verification_status: string;
}

export interface ChatResponse {
  answer: string;
  model_mode: string;
  key_metrics?: Array<{ label?: string; name?: string; value: string | number }> | Record<string, string | number> | null;
  table_data?: { headers?: string[]; rows?: Array<Array<string | number>> } | Array<Record<string, string | number>> | null;
  chart_data?: Record<string, unknown> | null;
  sources: string[];
  warnings?: string[];
  diagnostics?: Record<string, unknown> | null;
  sql_data?: Record<string, unknown> | null;
  calculations?: Record<string, unknown> | null;
  evidence: EvidenceItem[];
  suggested_followups: string[];
  disclaimer: string | null;
}

export interface EvidenceItem {
  text: string;
  source: string;
  page: number | null;
  year_range: string;
  relevance_score: number;
  citation: string;
}

export interface BudgetTotal {
  financial_year: string;
  financial_stage: string;
  total_amount_lakh: number;
  total_amount_crore: number;
  record_count: number;
  scope: string;
  note: string;
}

export interface ProgrammeItem {
  programme: string;
  pool: string | null;
  amount_lakh: number;
  amount_crore: number;
  share_pct: number;
  record_count: number;
}

export interface AllocationResult {
  label: string;
  disclaimer: string;
  scenario: string;
  total_budget_crore: number;
  total_budget_lakh: number;
  methodology: string;
  assumptions: string[];
  districts_included: number;
  allocations_lakh: Record<string, number>;
  allocations_crore: Record<string, number>;
  per_capita_rupees: Record<string, number>;
  shares_pct: Record<string, number>;
}

export interface SystemStatus {
  system: string;
  gpu: {
    available: boolean;
    device: string;
    gpu_name: string | null;
    vram_gb: number | null;
    adequate_for_qwen3_4b: boolean;
    note?: string;
  };
  slm: {
    loaded: boolean;
    mode: string;
    inference_active: boolean;
  };
  rag: {
    document_count: number;
    embeddings_available: boolean;
  };
  active_mode: string;
  capabilities: Record<string, boolean>;
}

// API functions
export const apiService = {
  // Districts
  getDistricts: () => api.get<{ total: number; districts: District[] }>('/api/districts'),
  getDistrictProfile: (id: number) => api.get<District & { budget_history: unknown[]; data_coverage: unknown }>(`/api/districts/${id}/profile`),
  getDistrictBudget: (id: number, year?: string, stage?: string) =>
    api.get(`/api/districts/${id}/budget`, { params: { year, stage } }),
  searchDistrict: (name: string) => api.get(`/api/districts/search/${encodeURIComponent(name)}`),

  // Budgets
  getStatewideBudget: (year: string, stage = 'PROPOSED_PIP') =>
    api.get<BudgetTotal>('/api/budgets/statewide', { params: { year, stage } }),
  getProgrammes: (year: string, stage = 'PROPOSED_PIP') =>
    api.get<{ programmes: ProgrammeItem[]; total_lakh: number }>('/api/budgets/programmes', { params: { year, stage } }),
  getBudgetGrowth: (year1: string, year2: string, stage = 'PROPOSED_PIP') =>
    api.get('/api/budgets/growth', { params: { year1, year2, stage } }),
  compareYears: (years: string, stage = 'PROPOSED_PIP') =>
    api.get('/api/budgets/compare', { params: { years, stage } }),
  getAvailableYears: () => api.get<{ available_years: string[]; available_stages: string[] }>('/api/budgets/available-years'),

  // Analytics
  getTrends: (stage = 'PROPOSED_PIP') => api.get('/api/analytics/trends', { params: { stage } }),
  getProgrammeSummary: (stage = 'PROPOSED_PIP') => api.get('/api/analytics/programmes/summary', { params: { stage } }),
  getDistrictsOverview: () => api.get('/api/analytics/districts/overview'),

  // Allocations
  recommendAllocation: (params: {
    total_budget_crore: number;
    districts?: string[];
    population_weight?: number;
    vulnerability_weight?: number;
  }) => api.post<AllocationResult>('/api/allocations/recommend', params),
  getScenarios: (params: { total_budget_crore: number }) =>
    api.post('/api/allocations/scenarios', { ...params, population_weight: 0.4, vulnerability_weight: 0.6 }),

  // Chat
  chat: (question: string, language = 'en') =>
    api.post<ChatResponse>('/api/chat', { question, language, include_evidence: true }),

  // Reports
  getDataQuality: () => api.get('/api/reports/data-quality'),
  getSources: () => api.get('/api/reports/sources'),
  exportCSV: (year?: string, stage?: string) => {
    const params = new URLSearchParams();
    if (year) params.set('year', year);
    if (stage) params.set('stage', stage);
    window.open(`${BASE_URL}/api/reports/export/csv?${params.toString()}`, '_blank');
  },

  // System
  getStatus: () => api.get<SystemStatus>('/api/system/status'),
};

export default apiService;
