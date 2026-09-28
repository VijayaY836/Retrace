import { fmtMonth, pct, STATUS } from "../api";

function Section({ n, title, tone, children }) {
  return (
    <section className="anim-rise">
      <h3 className={`flex items-center gap-2 text-[12px] font-bold uppercase tracking-wide ${tone}`}>
        <span className="flex h-4 w-4 items-center justify-center rounded-full bg-current text-[10px] text-white"><span className="text-white">{n}</span></span>{title}
      </h3>
      <div className="mt-1.5 pl-6 text-[13px] leading-snug">{children}</div>
    </section>
  );
}

export default function AnswerPanel({ result, shown, loading }) {
  if (loading || !result) {
    return (
      <section className="panel flex min-h-0 flex-col" aria-label="What we learned">
        <div className="panel-head"><h2 className="h-label">What we learned</h2></div>
        <p className="p-4 text-sm leading-relaxed text-ink-3">{loading ? "Reconstructing the history of learning…" : "RETRACE answers in four parts: what we believed, what we later saw, what we now know, and what remains unknown."}</p>
      </section>
    );
  }
  if (result.mode === "amnesia") {
    return (
      <section className="panel flex min-h-0 flex-col" aria-label="Answer without memory">
        <div className="panel-head"><h2 className="h-label">Answer without memory</h2></div>
        <div className="scroll-y flex-1 space-y-3 p-4 text-[13px]">
          <p className="rounded border-l-[3px] border-fault bg-fault-soft px-3 py-2 leading-snug">{result.answer.answer}</p>
          <ul className="list-disc space-y-1 pl-5">{result.answer.suggestions.map((s) => <li key={s}>{s}</li>)}</ul>
          <p className="border-t border-line pt-3 text-xs text-ink-3">Generic advice. It doesn't know NOVA tested this before, what the team concluded, or that the conclusion was later contradicted.</p>
        </div>
      </section>
    );
  }
  const s = result.sections;
  const a = result.analysis;
  const m = a.main_belief;
  const ready = shown.has("ANSWER");
  const tvn = a.then_vs_now;

  return (
    <section className="panel flex min-h-0 flex-col" aria-label="What we learned">
      <div className="panel-head"><h2 className="h-label">What we learned</h2>{m && shown.has("REVISE") && <span className={`chip ${STATUS[m.status].chip}`}>{STATUS[m.status].name}</span>}</div>
      <div className="scroll-y flex-1 space-y-3.5 p-4">
        {ready ? (
          <div className="anim-rise rounded border border-mem-mid bg-mem-soft px-3 py-2">
            <p className="font-display text-[18px] font-bold leading-tight">{result.written.headline}</p>
            <p className="mt-1 text-[13px] leading-snug text-ink">{result.written.answer}</p>
          </div>
        ) : <p className="text-sm text-ink-3">Working through the evidence…</p>}

        {s.believed && (
          <Section n="1" title="What we believed" tone="text-ink-2">
            <p className="font-semibold">“{s.believed.statement}”</p>
            <p className="text-ink-2">{s.believed.author}, {fmtMonth(s.believed.date)}, after {s.believed.source}
              {s.believed.source_result && <> ({s.believed.source_result.name}, <span className={s.believed.source_result.lift < 0 ? "text-fault" : "text-ok"}>{pct(s.believed.source_result.lift)}</span>)</>}</p>
          </Section>
        )}
        {shown.has("COMPARE") && (
          <Section n="2" title="What we later saw" tone="text-mem">
            {s.later.length ? (
              <ul className="space-y-1">
                {s.later.map((l) => (
                  <li key={l.id} className="flex gap-2">
                    <span className="w-16 shrink-0 text-ink-3">{fmtMonth(l.date)}</span>
                    {l.type === "experiment" ? (
                      <span><b>{l.id}</b> {l.name}: <span className={l.lift < 0 ? "text-fault" : "text-ok"}>{pct(l.lift)}</span>{" "}
                        <span className={`chip ${l.agrees ? "bg-ok-soft text-ok" : "bg-fault-soft text-fault"}`}>{l.agrees ? "agrees" : "disagrees"}</span></span>
                    ) : (
                      <span className="text-ink-2">{l.from_chat && <span className="chip mr-1 bg-hs-soft text-hs">from chat</span>}<i>{l.author}:</i> {l.text}</span>
                    )}
                  </li>
                ))}
              </ul>
            ) : <p className="text-ink-3">Nothing new since.</p>}
          </Section>
        )}
        {shown.has("REVISE") && (
          <Section n="3" title="What we now know" tone="text-fault">
            <p>{s.now_know}</p>
          </Section>
        )}
        {shown.has("COVERAGE") && (
          <Section n="4" title="What remains unknown" tone="text-warn">
            {s.unknown ? (
              <>
                <p className="font-semibold">{s.unknown.label}</p>
                <p className="text-ink-2">The most informative untested combination — see the <span className="font-semibold text-mem">Coverage map</span> tab for why.</p>
              </>
            ) : <p className="text-ink-3">Every combination has been tested.</p>}
            {s.planned.length > 0 && <p className="mt-1 text-hs">Already planned: {s.planned.map((p) => p.note).join(" ")}</p>}
          </Section>
        )}
        {ready && tvn && (
          <details className="rounded border border-line px-3 py-2" open={result.route.type === "still_applies"}>
            <summary className="cursor-pointer text-xs font-semibold text-ink-2">Then vs now: does {tvn.experiment} still apply?</summary>
            <table className="mt-2 w-full text-left text-[12px]">
              <thead className="text-ink-3"><tr><th className="font-semibold">Condition</th><th className="font-semibold">Then</th><th className="font-semibold">Now</th></tr></thead>
              <tbody>{tvn.rows.map((r) => <tr key={r.key} className={`border-t border-line ${r.changed ? "font-semibold" : ""}`}><td className="py-1">{r.label}</td><td>{r.then}</td><td className={r.changed ? (r.matters ? "text-fault" : "text-warn") : ""}>{r.now}{r.changed && r.matters ? " · matters" : ""}</td></tr>)}</tbody>
            </table>
            <p className="mt-1.5 text-[12px] text-ink">{tvn.verdict}</p>
          </details>
        )}
        {ready && result.reflection && (
          <details className="rounded bg-hs-soft px-3 py-2">
            <summary className="cursor-pointer text-xs font-semibold text-hs">Hindsight reflection</summary>
            <p className="mt-1.5 whitespace-pre-line text-xs">{result.reflection}</p>
          </details>
        )}
        {ready && result.mental_model?.content && (
          <details className="rounded bg-hs-soft px-3 py-2">
            <summary className="cursor-pointer text-xs font-semibold text-hs">Hindsight mental model: {result.mental_model.name} ({result.mental_model.versions} versions)</summary>
            <p className="mt-1.5 whitespace-pre-line text-xs">{result.mental_model.content}</p>
          </details>
        )}
      </div>
    </section>
  );
}