import { useState } from "react";

export default function AskPanel({ company, question, setQuestion, onAsk, busy, memoryOn, added, onAddResult, onAddDecision, onAddNote }) {
  const [note, setNote] = useState("");
  const submit = (q) => { const t = (q ?? question).trim(); if (t.length >= 3) onAsk(t); };
  return (
    <section className="panel flex min-h-0 flex-col" aria-label="Ask RETRACE">
      <div className="panel-head"><h2 className="h-label">Ask RETRACE</h2></div>
      <div className="scroll-y flex-1 space-y-4 p-3.5">
        <div>
          <textarea className="field resize-none pr-9" rows={3} value={question} onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
            placeholder="e.g. Should we bring gamified onboarding back?" aria-label="Your question" />
          <button className={`mt-2 w-full ${memoryOn ? "btn-primary" : "btn bg-fault text-white hover:bg-[#b82a3f]"}`} onClick={() => submit()} disabled={busy || question.trim().length < 3}>
            {busy ? "Thinking…" : memoryOn ? "Ask with memory" : "Ask without memory"}
          </button>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-ink-2">Try asking</h3>
          <ul className="mt-1.5 space-y-1">
            {company?.suggested
              ?.filter((s) => s.text.trim().toLowerCase() !== question.trim().toLowerCase())
              .map((s) => (
              <li key={s.text}>
                <button onClick={() => { setQuestion(s.text); submit(s.text); }} disabled={busy}
                  className="w-full rounded border border-line bg-sunk px-2.5 py-1.5 text-left text-[13px] leading-snug text-ink hover:border-mem hover:bg-mem-soft">
                  {s.text}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="border-t border-line pt-3">
          <h3 className="text-xs font-semibold text-ink-2">Add to memory</h3>
          <p className="mt-0.5 text-[11px] text-ink-3">New evidence is retained in Hindsight and RETRACE re-judges its beliefs.</p>
          <div className="mt-2 space-y-1.5">
            <button onClick={onAddResult} disabled={busy || added.result} className="btn-ghost w-full justify-start text-left text-[13px]">
              {added.result ? "✓ EXP-24 result added" : "New result: EXP-24 (2 pushes/day, +3%)"}
            </button>
            <button onClick={onAddDecision} disabled={busy || added.decision} className="btn-ghost w-full justify-start text-left text-[13px]">
              {added.decision ? "✓ Decision recorded" : "Decide: run the iOS test as EXP-25"}
            </button>
            <div className="flex gap-1.5">
              <input className="field py-1.5 text-[13px]" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Share an interpretation…" aria-label="Team note" />
              <button className="btn-ghost shrink-0 px-2.5" disabled={busy || note.trim().length < 3} onClick={() => { onAddNote(note.trim()); setNote(""); }}>Save</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}