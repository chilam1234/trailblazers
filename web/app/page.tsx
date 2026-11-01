"use client";

import { useEffect, useMemo, useState } from "react";
import { getCompanies, resumeHitl, runResearch } from "../lib/api";
import type { Company, ResearchResult } from "../lib/types";

const STARTERS: Array<{ label: string; question: string; hitl?: boolean }> = [
  { label: "NVDA briefing", question: "Brief NVIDIA data-center mix and China export-control risk for the PM." },
  { label: "AAPL 10-K", question: "Summarize Apple Services mix and Greater China from the latest 10-K." },
  { label: "MSFT capex", question: "How does Microsoft Azure growth compare with capex intensity?" },
  { label: "Add XOM", question: "Add Exxon to the coverage watchlist.", hitl: true },
  { label: "Desk note", question: "File a desk note: JPM NII peak-and-fade risk into the morning meeting.", hitl: true },
];

export default function DeskPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [question, setQuestion] = useState(STARTERS[0].question);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [edit, setEdit] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    void getCompanies().then(setCompanies);
  }, [result?.status]);

  const proposedText = useMemo(
    () => JSON.stringify(result?.hitl?.proposed ?? result?.proposed ?? {}, null, 2),
    [result],
  );

  useEffect(() => {
    setEdit(proposedText);
  }, [proposedText]);

  async function run(next = question) {
    setBusy(true);
    setError("");
    try {
      const out = await runResearch(next);
      setResult(out);
    } catch (err) {
      setError(err instanceof Error ? err.message : "research failed");
    } finally {
      setBusy(false);
    }
  }

  async function decide(action: "approve" | "reject" | "edit") {
    if (!result) return;
    setBusy(true);
    setError("");
    try {
      let proposed: Record<string, unknown> | undefined;
      if (action === "edit" || action === "approve") {
        proposed = JSON.parse(edit || "{}") as Record<string, unknown>;
      }
      const out = await resumeHitl(result.thread_id, action, proposed);
      setResult(out);
      setCompanies(await getCompanies());
    } catch (err) {
      setError(err instanceof Error ? err.message : "HITL failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="layout">
      <aside className="side">
        <h2>COVERAGE UNIVERSE</h2>
        {companies.map((c) => (
          <div className="ticker" key={c.ticker}>
            <b>{c.ticker}</b>
            <span className="tag">{c.on_book ? "on book" : c.pod}</span>
          </div>
        ))}
        <div className="starters">
          <h2>STARTERS</h2>
          {STARTERS.map((s) => (
            <button
              key={s.label}
              className="starter"
              onClick={() => {
                setQuestion(s.question);
                void run(s.question);
              }}
            >
              {s.label}
              {s.hitl ? <span className="hitl-tag">HITL</span> : null}
            </button>
          ))}
        </div>
      </aside>
      <main className="main">
        <div className="ask">
          <label>QUESTION FOR THE DESK</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter") void run();
            }}
          />
          <div className="ask-row">
            <span>Fixture EDGAR/news. No keys required. ⌘/Ctrl+Enter to run.</span>
            <button className="btn primary" disabled={busy || !question.trim()} onClick={() => void run()}>
              {busy ? "Running…" : "Run research"}
            </button>
          </div>
        </div>
        {error ? <p className="fail">{error}</p> : null}
        {result?.steps?.length ? (
          <div className="steps">
            {result.steps.map((step) => (
              <span className="step" key={step.name}>
                {step.name} · {step.detail}
              </span>
            ))}
            {result.cache ? <span className="step">{result.cache}</span> : null}
          </div>
        ) : null}
        {result?.hitl ? (
          <section className="hitl">
            <h2>HUMAN IN THE LOOP</h2>
            <div>{result.hitl.title}</div>
            <p className="lede">{result.hitl.detail}</p>
            <div className="cols">
              <div className="col">
                <h3>CURRENT</h3>
                <pre>
                  {result.hitl.current
                    ? JSON.stringify(result.hitl.current, null, 2)
                    : "— not on watchlist —"}
                </pre>
              </div>
              <div className="col">
                <h3>PROPOSED (EDITABLE)</h3>
                <textarea value={edit} onChange={(e) => setEdit(e.target.value)} style={{ width: "100%", minHeight: 140, background: "transparent", color: "inherit", border: 0 }} />
              </div>
            </div>
            <div className="actions">
              <button className="btn primary" disabled={busy} onClick={() => void decide("approve")}>
                Approve
              </button>
              <button className="btn" disabled={busy} onClick={() => void decide("edit")}>
                Save edit & resume
              </button>
              <button className="btn danger" disabled={busy} onClick={() => void decide("reject")}>
                Reject
              </button>
            </div>
          </section>
        ) : null}
        {result ? (
          <article className="brief">
            <h2>
              {result.status === "paused" ? "Paused for desk approval" : "Cited briefing"}
            </h2>
            {result.briefing}
            {result.citations.length ? (
              <div className="cites">
                {result.citations.map((c) => (
                  <span className="cite" key={c.id} title={c.excerpt}>
                    {c.id}
                  </span>
                ))}
              </div>
            ) : null}
          </article>
        ) : null}
      </main>
    </div>
  );
}
