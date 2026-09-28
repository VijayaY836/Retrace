import { fmtDate, fmtMonth, liftTone, pct, STATUS } from "../api";

export default function LearningTimeline({ a, shown }) {
  const t = a.timeline;
  const start = new Date(t.range[0]).getTime();
  const end = new Date(t.range[1]).getTime() + 1000 * 3600 * 24 * 20;
  const x = (s) => Math.max(0, Math.min(100, ((new Date(s).getTime() - start) / (end - start)) * 100));
  const years = [];
  for (let y = new Date(t.range[0]).getFullYear() + 1; y <= new Date(t.range[1]).getFullYear(); y++) years.push(y);
  const exps = t.experiments;
  const cleanPairs = a.clean.slice(0, 5);
  const posOf = Object.fromEntries(exps.map((e) => [e.id, x(e.date)]));
  const compared = shown.has("COMPARE");
  const edge = (v) => (v < 6 ? "translateX(0)" : v > 94 ? "translateX(-100%)" : "translateX(-50%)");
  const revised = shown.has("REVISE");

  return (
    <div className="px-5 pb-3 pt-2">
      {/* axis */}
      <p className="mb-1 text-[11px] text-ink-3">{a.counts.experiments} experiments in {a.area_label.toLowerCase()} · {a.counts.usable} usable · {a.counts.set_aside} set aside · hover any point for details</p>
      <div className="relative h-5 border-b border-line text-[11px] text-ink-3">
        <span className="absolute left-0">{fmtMonth(t.range[0])}</span>
        {years.map((y) => (
          <span key={y} className="absolute -translate-x-1/2" style={{ left: `${x(`${y}-01-01`)}%` }}>{y}</span>
        ))}
        <span className="absolute right-0 font-semibold text-mem">Today</span>
      </div>

      {/* experiments */}
      <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-ink-3">Experiments · {a.area_label}</p>
      <div className="relative h-[64px]">
        {exps.map((e, i) => (
          <div key={e.id} className={`anim-rise absolute flex flex-col ${x(e.date) > 94 ? "items-end" : x(e.date) < 6 ? "items-start" : "items-center"}`} style={{ left: `${x(e.date)}%`, top: i % 2 ? 26 : 0, animationDelay: `${i * 0.05}s`, transform: edge(x(e.date)) }}
            title={`${e.id} ${e.name} (${fmtDate(e.date)})\nTeam said: "${e.interpretation}"${e.quality !== "ok" ? `\nFlagged: ${e.quality}` : ""}`}>
            <span className={`whitespace-nowrap text-[11px] font-bold ${liftTone(e)}`}>{e.id.replace("EXP-", "E")} {pct(e.lift)}</span>
            <span className={`mt-0.5 h-3 w-3 rounded-full ring-2 ring-surface ${e.quality !== "ok" ? "border-2 border-dashed border-ink-3 bg-surface" :
              e.direction === "positive" ? "bg-ok" : e.direction === "negative" ? "bg-fault" : "bg-ink-3"}`} />
          </div>
        ))}
      </div>

      {/* clean comparison arcs */}
      <div className="relative h-8">
        {compared && (
          <svg className="absolute inset-0 h-full w-full overflow-visible" viewBox="0 0 100 30" preserveAspectRatio="none" aria-hidden="true">
            {cleanPairs.map((c, i) => {
              const x1 = posOf[c.a], x2 = posOf[c.b];
              if (x1 == null || x2 == null) return null;
              const strongest = a.strongest && c.a === a.strongest.a && c.b === a.strongest.b;
              return <path key={i} d={`M ${x1} 2 Q ${(x1 + x2) / 2} ${14 + i * 3} ${x2} 2`} fill="none" stroke={strongest ? "#2458E6" : "#B9CCF8"}
                strokeWidth={strongest ? 2.5 : 1.5} vectorEffect="non-scaling-stroke" className="anim-rise" />;
            })}
          </svg>
        )}
        {compared && a.strongest && (
          <span className="absolute right-0 top-3 rounded-sm bg-mem-soft px-1.5 text-[11px] font-semibold text-mem">
            Clean comparison: {a.strongest.a} vs {a.strongest.b}, only {a.strongest.changes[0].label} changed
          </span>
        )}
      </div>

      {/* product changes */}
      {t.product_changes.length > 0 && (
        <>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-3">Product changes</p>
          <div className="relative mb-1 h-5">
            {t.product_changes.map((p) => (
              <span key={p.id} className="absolute h-3 w-3 -translate-x-1/2 rotate-45 bg-ink/70" style={{ left: `${x(p.date)}%`, top: 4 }} title={`${fmtDate(p.date)}: ${p.text}`} />
            ))}
          </div>
        </>
      )}

      {/* belief lanes */}
      <p className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-ink-3">What the team believed</p>
      <div className="mt-1 space-y-2.5">
        {t.beliefs.map((b) => {
          const hist = revised ? b.history : b.history.slice(0, 1);
          return (
            <div key={b.id}>
              <div className="flex items-baseline gap-2">
                <p className={`text-[13px] font-semibold ${revised && b.status === "revised" ? "text-ink-2 line-through decoration-fault" : "text-ink"}`}>“{b.statement}”</p>
                {revised && <span className={`chip ${STATUS[b.status].chip}`}>{STATUS[b.status].name}</span>}
              </div>
              <div className="relative mt-1 h-2.5 rounded-full bg-sunk">
                {hist.map((h, i) => {
                  const from = x(h.date), to = i + 1 < hist.length ? x(hist[i + 1].date) : 100;
                  return <span key={i} className={`anim-rise absolute inset-y-0 rounded-full ${STATUS[h.status].bar}`} style={{ left: `${from}%`, width: `${Math.max(0.8, to - from)}%` }}
                    title={`${fmtDate(h.date)}: ${STATUS[h.status].name} (after ${h.by})`} />;
                })}
              </div>
              {revised && hist.length > 1 && (
                <div className="relative h-4 text-[10px] text-ink-2">
                  {hist.slice(1).map((h, i) => (
                    <span key={i} className="absolute whitespace-nowrap" style={{ left: `${x(h.date)}%`, transform: edge(x(h.date)) }}>
                      {STATUS[h.status].name} after {h.by}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* notes */}
      {t.notes.length > 0 && (
        <>
          <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-ink-3">Later observations and team notes</p>
          <div className="relative h-5">
            {t.notes.map((n) => (
              <span key={n.id} className={`absolute h-3 w-3 -translate-x-1/2 rounded-sm ${n.from_chat ? "bg-hs" : "bg-mem-mid"}`} style={{ left: `${x(n.date)}%`, top: 4 }}
                title={`${fmtMonth(n.date)} · ${n.author}: ${n.text}`} />
            ))}
          </div>
        </>
      )}

      <div className="mt-2 flex flex-wrap gap-3 border-t border-line pt-2 text-[11px] text-ink-3">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-ok" />positive</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-fault" />negative</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-ink-3" />no effect</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full border border-dashed border-ink-3" />flagged</span>
        <span className="flex items-center gap-1"><span className="h-0.5 w-4 bg-mem" />clean comparison</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-hs" />from team chat</span>
      </div>
    </div>
  );
}
