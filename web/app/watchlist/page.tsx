"use client";

import { useEffect, useState } from "react";
import { getWatchlist } from "../../lib/api";

type Book = Awaited<ReturnType<typeof getWatchlist>>;

export default function WatchlistPage() {
  const [book, setBook] = useState<Book>({ entries: [], notes: [] });

  useEffect(() => {
    void getWatchlist().then(setBook);
  }, []);

  return (
    <div className="page">
      <h2 style={{ letterSpacing: "0.12em", color: "var(--muted)", fontSize: 12, margin: 0 }}>SHARED BOOK</h2>
      <h1>Watchlist</h1>
      <p className="lede">
        Seeded with AAPL and NVDA. Adds and drops only land after a HITL approve on the desk —
        this page is the post-approval book.
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Name</th>
            <th>Pod</th>
            <th>Priority</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          {book.entries.map((row) => (
            <tr key={row.ticker}>
              <td>{row.ticker}</td>
              <td>{row.name}</td>
              <td>{row.pod}</td>
              <td>{row.priority}</td>
              <td>{row.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2 style={{ marginTop: 36 }}>Desk notes</h2>
      {book.notes.length === 0 ? (
        <p className="lede">No approved notes in the morning book.</p>
      ) : (
        book.notes.map((note, i) => (
          <article className="brief" key={`${note.ticker}-${i}`}>
            <h2>{note.title}</h2>
            {note.body}
          </article>
        ))
      )}
    </div>
  );
}
