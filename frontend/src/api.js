async function call(path, opts = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { msg = (await res.json()).detail || msg; } catch {}
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return res.json();
}

export const api = {
  health: () => call("/health"),
  company: () => call("/company"),
  ask: (question, memory) => call("/ask", { method: "POST", body: { question, memory } }),
  addResult: () => call("/evidence/demo", { method: "POST" }),
  addDecision: () => call("/decision/demo", { method: "POST" }),
  addNote: (text, topic) => call("/evidence/note", { method: "POST", body: { text, topic } }),
  reset: () => call("/demo/reset", { method: "POST" }),
};

export const pct = (x) => (Math.abs(x) < 0.01 ? `${(x * 100).toFixed(1)}%` : `${x > 0 ? "+" : ""}${Math.round(x * 100)}%`).replace(/^(\d)/, "+$1");
export const fmtDate = (s) => new Date(s).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
export const fmtMonth = (s) => new Date(s).toLocaleDateString("en-IN", { month: "short", year: "numeric" });

export const STATUS = {
  held_up: { name: "Held up", chip: "bg-ok text-white", bar: "bg-ok", soft: "bg-ok-soft text-ok" },
  challenged: { name: "Challenged", chip: "bg-warn text-white", bar: "bg-warn", soft: "bg-warn-soft text-warn" },
  revised: { name: "Revised", chip: "bg-fault text-white", bar: "bg-fault", soft: "bg-fault-soft text-fault" },
  weak_basis: { name: "Weak basis", chip: "border border-dashed border-ink-3 text-ink-2", bar: "bg-ink-3/40", soft: "bg-sunk text-ink-2" },
  untested_since: { name: "Untested", chip: "bg-sunk text-ink-3", bar: "bg-line", soft: "bg-sunk text-ink-3" },
};

export const liftTone = (e) =>
  e.quality && e.quality !== "ok" ? "text-ink-3" : e.direction === "positive" ? "text-ok" : e.direction === "negative" ? "text-fault" : "text-ink-2";
