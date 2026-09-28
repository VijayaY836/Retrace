import { useEffect, useState } from "react";
import LearningTimeline from "./LearningTimeline";
import Comparisons from "./Comparisons";
import CoverageMap from "./CoverageMap";

const STEPS = ["Recalling experiments, beliefs and later evidence", "Finding clean comparisons", "Re-judging the team's beliefs", "Mapping what was never tested", "Writing the answer"];

export default function CenterPanel({ result, shown, loading }) {
  const [tab, setTab] = useState("timeline");
  useEffect(() => {
    if (result?.route?.type === "what_next") setTab("coverage");
    else setTab("timeline");
  }, [result]);
  const a = result?.mode === "memory" ? result.analysis : null;
  const tabs = [["timeline", "Learning timeline"], ["comparisons", `Clean comparisons${a ? ` (${a.counts.clean})` : ""}`], ["coverage", "Coverage map"]];

  return (
    <section className="panel flex min-h-0 flex-col" aria-label="Evidence">
      <div className="flex items-center justify-between gap-3 border-b border-line px-4">
        <div role="tablist" className="flex gap-4">
          {tabs.map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} disabled={!a} onClick={() => setTab(id)}
              className={`-mb-px whitespace-nowrap border-b-2 py-2.5 text-sm font-semibold disabled:text-ink-3/60 ${tab === id && a ? "border-mem text-mem" : "border-transparent text-ink-2 hover:text-ink"}`}>
              {label}
            </button>
          ))}
        </div>
        {a && <span className="hidden whitespace-nowrap text-[11px] font-semibold text-ink-2 xl:inline">{a.topic.label}</span>}
      </div>
      <div className="scroll-y min-h-0 flex-1">
        {loading && (
          <div className="p-5">
            <p className="font-display text-lg font-semibold text-mem">Reading NOVA's memory…</p>
            <ol className="mt-3 space-y-1.5">{STEPS.map((s, i) => <li key={s} className="anim-rise text-sm text-ink-2" style={{ animationDelay: `${i * 0.3}s` }}><span className="mr-2 text-ink-3">{i + 1}.</span>{s}</li>)}</ol>
          </div>
        )}
        {!loading && !a && (
          <div className="flex h-full items-center justify-center p-8">
            <p className="max-w-sm text-center text-sm leading-relaxed text-ink-3">
              {result?.mode === "amnesia" ? "Amnesia mode has no experiment history. It can only give generic advice."
                : "Ask a question. The experiments, what the team believed and how that belief changed will line up here over time."}
            </p>
          </div>
        )}
        {!loading && a && tab === "timeline" && <LearningTimeline a={a} shown={shown} />}
        {!loading && a && tab === "comparisons" && <Comparisons a={a} />}
        {!loading && a && tab === "coverage" && <CoverageMap a={a} />}
      </div>
    </section>
  );
}
