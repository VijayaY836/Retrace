import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import Header from "./components/Header";
import AskPanel from "./components/AskPanel";
import CenterPanel from "./components/CenterPanel";
import AnswerPanel from "./components/AnswerPanel";
import TracePanel from "./components/TracePanel";

const STEP_MS = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 650;

export default function App() {
  const [company, setCompany] = useState(null);
  const [health, setHealth] = useState(null);
  const [memoryOn, setMemoryOn] = useState(true);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [revealed, setRevealed] = useState(0);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [added, setAdded] = useState({ result: false, decision: false });
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const timer = useRef();

  useEffect(() => {
    api.company().then(setCompany).catch(() => setError("Cannot reach the RETRACE backend on port 8000. Is it running?"));
    api.health().then(setHealth).catch(() => {});
  }, []);

  useEffect(() => {
    clearInterval(timer.current);
    if (result?.mode !== "memory") return;
    if (!STEP_MS) { setRevealed(result.trace.length); return; }
    setRevealed(1);
    timer.current = setInterval(() => setRevealed((r) => { if (r >= result.trace.length) { clearInterval(timer.current); return r; } return r + 1; }), STEP_MS);
    return () => clearInterval(timer.current);
  }, [result]);

  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(""), 3500); return () => clearTimeout(t); }, [toast]);

  const shown = new Set(result?.mode === "memory" ? result.trace.slice(0, revealed).map((t) => t.op) : []);

  const guard = async (fn) => { setError(""); setBusy(true); try { await fn(); } catch (e) { setError(e.message); } setBusy(false); };

  const ask = (q, mem = memoryOn) => guard(async () => {
    setQuestion(q); setLoading(true); setResult(null); setRevealed(0);
    try { setResult(await api.ask(q, mem)); } finally { setLoading(false); }
  });

  const addResult = async () => { await guard(async () => { await api.addResult(); setAdded((s) => ({ ...s, result: true })); setToast("EXP-24 retained in Hindsight. Re-checking the push belief…"); }); ask("Do push notifications hurt retention?", true); setMemoryOn(true); };
  const addDecision = async () => { await guard(async () => { await api.addDecision(); setAdded((s) => ({ ...s, decision: true })); setToast("Decision retained: EXP-25 planned."); }); ask("What should we test next for gamified onboarding?", true); setMemoryOn(true); };
  const addNote = async (text) => { await guard(async () => { await api.addNote(text, result?.topic?.id); setToast("Note retained as a dated team interpretation."); }); if (question) ask(question, true); };
  const reset = () => guard(async () => { await api.reset(); setResult(null); setQuestion(""); setAdded({ result: false, decision: false }); setMemoryOn(true); setToast("Demo reset."); });
  const toggle = (on) => { setMemoryOn(on); setResult(null); setRevealed(0); };

  return (
    <div className="flex min-h-screen flex-col lg:h-screen lg:overflow-hidden">
      <Header company={company} health={health} memoryOn={memoryOn} setMemoryOn={toggle} onReset={reset} busy={busy} />
      {error && <p role="alert" className="shrink-0 border-b border-fault-mid bg-fault-soft px-4 py-1.5 text-sm text-fault">{error}</p>}
      {toast && <p role="status" className="anim-rise fixed right-4 top-16 z-30 rounded border border-hs/40 bg-hs-soft px-3 py-2 text-sm font-semibold text-hs shadow-lg">{toast}</p>}
      <main className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-3 pb-0 lg:grid-cols-[290px_minmax(0,1fr)_400px] [&>*]:min-h-[360px] lg:[&>*]:min-h-0">
        <AskPanel company={company} question={question} setQuestion={setQuestion} onAsk={(q) => ask(q)} busy={busy} memoryOn={memoryOn}
          added={added} onAddResult={addResult} onAddDecision={addDecision} onAddNote={addNote} />
        <CenterPanel result={result} shown={shown} loading={loading} />
        <AnswerPanel result={result} shown={shown} loading={loading} />
      </main>
      <div className="shrink-0 p-3"><TracePanel result={result} revealed={revealed} backend={health?.memory_backend} /></div>
    </div>
  );
}
