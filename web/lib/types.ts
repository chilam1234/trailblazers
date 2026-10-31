export type Company = {
  ticker: string;
  name: string;
  sector: string;
  pod: string;
  priority: string;
  on_book: boolean;
  reason: string;
};

export type Citation = {
  id: string;
  kind: string;
  ticker: string;
  title: string;
  filed: string;
  excerpt: string;
};

export type Step = { name: string; detail: string; ms: number };

export type HitlPayload = {
  title: string;
  detail?: string;
  intent?: string;
  current?: Record<string, unknown> | null;
  proposed?: Record<string, unknown> | null;
};

export type ResearchResult = {
  thread_id: string;
  status: string;
  intent: string;
  tickers: string[];
  question: string;
  briefing: string;
  citations: Citation[];
  provider: string;
  grounded: boolean;
  healed: boolean;
  tools_used: string[];
  steps: Step[];
  hitl: HitlPayload | null;
  proposed: Record<string, unknown> | null;
  cache?: string;
  elapsed_ms?: number;
};

export type Status = {
  provider: string;
  p50_ms: number;
  cache_hits: number;
  cache_total: number;
  rate_remaining: number;
};

export type EvalRow = {
  id: string;
  query: string;
  score: number;
  misses: string[];
  hitl: boolean;
  elapsed_ms: number;
};

export type EvalRun = {
  gate: number;
  mean: number | null;
  cases: number;
  p50_ms?: number;
  passed?: boolean;
  results: EvalRow[];
};
