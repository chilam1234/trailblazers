import type { Company, EvalRun, ResearchResult, Status } from "./types";

export async function getStatus(): Promise<Status> {
  const resp = await fetch("/api/status", { cache: "no-store" });
  if (!resp.ok) {
    return { provider: "fixture", p50_ms: 0, cache_hits: 0, cache_total: 0, rate_remaining: 0 };
  }
  return resp.json();
}

export async function getCompanies(): Promise<Company[]> {
  const resp = await fetch("/api/companies", { cache: "no-store" });
  return resp.ok ? resp.json() : [];
}

export async function getWatchlist(): Promise<{
  entries: Array<{ ticker: string; name: string; pod: string; priority: string; reason: string }>;
  notes: Array<{ ticker: string; title: string; body: string }>;
}> {
  const resp = await fetch("/api/watchlist", { cache: "no-store" });
  return resp.ok ? resp.json() : { entries: [], notes: [] };
}

export async function runResearch(question: string, threadId?: string): Promise<ResearchResult> {
  const resp = await fetch("/api/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, thread_id: threadId }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function resumeHitl(
  threadId: string,
  action: "approve" | "reject" | "edit",
  proposed?: Record<string, unknown>,
): Promise<ResearchResult> {
  const resp = await fetch("/api/hitl/resume", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, action, proposed }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function getEvals(): Promise<EvalRun> {
  const resp = await fetch("/api/evals", { cache: "no-store" });
  return resp.ok ? resp.json() : { gate: 0.92, mean: null, cases: 0, results: [] };
}

export async function runEvals(): Promise<EvalRun> {
  const resp = await fetch("/api/evals/run", { method: "POST" });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function getTraces(): Promise<{ events: Array<Record<string, unknown>> }> {
  const resp = await fetch("/api/traces", { cache: "no-store" });
  return resp.ok ? resp.json() : { events: [] };
}
