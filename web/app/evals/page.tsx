"use client";

import { useEffect, useState } from "react";
import { getEvals, runEvals } from "../../lib/api";
import type { EvalRun } from "../../lib/types";

export default function EvalsPage() {
  const [run, setRun] = useState<EvalRun | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void getEvals().then(setRun);
  }, []);

  async function rerun() {
    setBusy(true);
    try {
      setRun(await runEvals());
    } finally {
      setBusy(false);
    }
  }

  const passed = Boolean(run?.passed);
  return (
    <div className="page">
      <h2 style={{ letterSpacing: "0.12em", color: "var(--muted)", fontSize: 12, margin: 0 }}>
        WEEK 10 / PHASE 4 GATE
      </h2>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "end" }}>
        <div>
          <h1>Eval board</h1>
          <p className="lede">
            Twenty goldens over the fixture spine. CI fails under a 0.92 mean. Research cases must
            not fire HITL; watchlist / desk-note cases must.
          </p>
        </div>
        <button className="btn primary" disabled={busy} onClick={() => void rerun()}>
          {busy ? "Running…" : "Re-run gate"}
        </button>
      </div>
      <div className="kpis">
        <div className="kpi">
          <span>GATE</span>
          <strong className={passed ? "pass" : "fail"}>{run?.mean == null ? "—" : passed ? "pass" : "fail"}</strong>
        </div>
        <div className="kpi">
          <span>MEAN</span>
          <strong>{run?.mean == null ? "—" : run.mean.toFixed(4)}</strong>
        </div>
        <div className="kpi">
          <span>CASES</span>
          <strong>{run?.cases ?? 0}</strong>
        </div>
        <div className="kpi">
          <span>P50</span>
          <strong>{run?.p50_ms != null ? `${run.p50_ms.toFixed(2)}ms` : "—"}</strong>
        </div>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Query</th>
            <th>Score</th>
            <th>Misses</th>
          </tr>
        </thead>
        <tbody>
          {(run?.results ?? []).map((row) => (
            <tr key={row.id}>
              <td>{row.id}</td>
              <td>{row.query}</td>
              <td className={row.score >= 1 ? "pass" : "fail"}>{row.score.toFixed(2)}</td>
              <td>{row.misses.length ? row.misses.join(", ") : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
