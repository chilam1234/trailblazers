"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getStatus } from "../lib/api";
import type { Status } from "../lib/types";

const LINKS = [
  { href: "/", label: "Desk" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/evals", label: "Eval board" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    void getStatus().then(setStatus);
  }, [path]);

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">MERIDIAN RESEARCH DESK</div>
        <nav className="nav">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} className={path === link.href ? "active" : ""}>
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="chips">
          <span className="chip">PROVIDER {status?.provider ?? "fixture"}</span>
          <span className="chip">P50 {status ? `${status.p50_ms.toFixed(0)}ms` : "—"}</span>
          <span className="chip">
            CACHE {status ? `${status.cache_hits}/${status.cache_total}` : "0/0"}
          </span>
          <Link href="/traces" className="chip">
            Traces
          </Link>
        </div>
      </header>
      {children}
    </div>
  );
}
