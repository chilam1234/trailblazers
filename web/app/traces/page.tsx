"use client";

import { useEffect, useState } from "react";
import { getTraces } from "../../lib/api";

export default function TracesPage() {
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    void getTraces().then((payload) => setEvents(payload.events ?? []));
  }, []);

  return (
    <div className="page">
      <h1>Traces</h1>
      <p className="lede">
        In-process OpenTelemetry spans plus the desk&apos;s own latency log. No vendor backend
        required — the gateway records plan / retrieve / draft / cache hits here.
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>ms</th>
            <th>Attrs</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event, i) => (
            <tr key={`${String(event.name)}-${i}`}>
              <td>{String(event.name ?? "")}</td>
              <td>{String(event.elapsed_ms ?? "")}</td>
              <td>
                <code>{JSON.stringify(event.attrs ?? {})}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
