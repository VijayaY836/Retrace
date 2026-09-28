import { pct } from "../api";

const tone = (v) => (v > 0.005 ? "text-ok" : v < -0.005 ? "text-fault" : "text-ink-2");

export default function Comparisons({ a }) {
  return (
    <div className="space-y-4 px-4 py-3">
      <section>
        <h3 className="text-xs font-semibold text-mem">Clean comparisons: exactly one condition changed ({a.clean.length})</h3>
        <p className="text-[11px] text-ink-3">Only these can isolate what made the difference.</p>
        <ul className="mt-2 space-y-1.5">
          {a.clean.map((c) => {
            const strongest = a.strongest && a.strongest.a === c.a && a.strongest.b === c.b;
            return (
              <li key={c.a + c.b} className={`grid grid-cols-[110px_1fr_auto] items-center gap-3 rounded border px-3 py-2 ${strongest ? "border-mem bg-mem-soft" : "border-line"}`}>
                <span className="font-display text-[15px] font-bold">{c.a} vs {c.b}</span>
                <span className="text-[13px]"><span className="chip mr-1.5 bg-mem text-white">only {c.changes[0].label}</span>{c.changes[0].from} → {c.changes[0].to}</span>
                <span className="whitespace-nowrap font-display text-[15px] font-bold">
                  <span className={tone(c.lift_a)}>{pct(c.lift_a)}</span><span className="px-1 text-ink-3">→</span><span className={tone(c.lift_b)}>{pct(c.lift_b)}</span>
                </span>
              </li>
            );
          })}
          {!a.clean.length && <li className="text-sm text-ink-3">No clean comparisons yet in this area.</li>}
        </ul>
      </section>
      <section>
        <h3 className="text-xs font-semibold text-warn">Confounded: several things changed at once ({a.counts.confounded})</h3>
        <p className="text-[11px] text-ink-3">Supporting context only. These cannot isolate a cause.</p>
        <ul className="mt-2 space-y-1">
          {a.confounded.slice(0, 6).map((c) => (
            <li key={c.a + c.b} className="flex flex-wrap items-baseline gap-x-2 rounded border border-dashed border-warn-mid px-3 py-1.5 text-[13px]">
              <span className="font-semibold">{c.a} vs {c.b}</span>
              <span className="text-ink-2">differs in {c.changes.map((x) => x.label).join(", ")}</span>
              <span className="ml-auto whitespace-nowrap text-ink-2">{pct(c.lift_a)} → {pct(c.lift_b)}</span>
            </li>
          ))}
        </ul>
      </section>
      {a.set_aside.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-ink-2">Set aside ({a.set_aside.length})</h3>
          <ul className="mt-1.5 space-y-1 text-[13px]">
            {a.set_aside.map((s) => <li key={s.id}><span className="font-semibold text-ink-2 line-through">{s.id} {s.name}</span> <span className="text-ink-3">{s.reason}</span></li>)}
          </ul>
        </section>
      )}
    </div>
  );
}
