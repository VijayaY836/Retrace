"""RETRACE pipeline: RETAIN → RECALL → COMPARE → REVISE → COVERAGE → ANSWER."""
import asyncio
import json
import time
import uuid
from datetime import datetime

from . import engine, ledger, llm
from .config import COMPANY, TOPICS
from .memory import get_memory, safe
from .records import record_id

STATE = {"last_topic": None}
KIND_LABEL = {"experiment": "experiments", "belief": "beliefs", "observation": "observations", "note": "team notes",
              "product_state": "product changes", "event": "external events", "decision": "decisions", "qa": "past answers"}


async def gather(topic: dict) -> tuple[list[dict], dict]:
    mem = get_memory()
    area, label = topic["area"], topic["label"]
    queries = [
        (f"Experiments about {label.lower()} in {area}: conditions, results and interpretations", [f"area:{area}"], "experiments in this area"),
        (f"Team beliefs and conclusions about {label.lower()}", ["kind:belief"], "team beliefs"),
        (f"Research, observations and team notes about {label.lower()}", ["kind:observation", "kind:note"], "later observations"),
        ("How the product changed over time and what it looks like today", ["kind:product_state"], "product changes"),
        ("Outages, sales and other external events", ["kind:event"], "external events"),
        (f"Planned experiments and decisions for {area}", ["kind:decision"], "planned decisions"),
        (f"Anything mentioning {topic['keywords'][0]}", None, "same word, any area"),
        (f"What did the team say in chat about {label.lower()}?", None, "team chat"),
    ]
    t0 = time.time()
    results = await asyncio.gather(*[safe(mem.recall(q, tags=t), default=[], timeout=40) for q, t, _ in queries])
    ms = int((time.time() - t0) * 1000)
    known = ledger.known_ids()
    recs, per_query, raw = {}, [], 0
    for (q, t, lab), hits in zip(queries, results):
        raw += len(hits)
        ids = []
        for h in hits:
            r = h.get("record")
            if not r:
                continue
            rid = record_id(r)
            if rid in known or r.get("source") == "chat":
                recs[rid] = r
                ids.append(rid)
        per_query.append({"label": lab, "query": q, "tags": t, "memories": len(hits), "records": sorted(set(ids))})
    backfilled = [rid for rid in ledger.demo_ids() if rid not in recs]
    for rid in backfilled:
        recs[rid] = ledger.get(rid)
    counts = {}
    for r in recs.values():
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    summary = ", ".join(f"{v} {KIND_LABEL.get(k, k)}" for k, v in sorted(counts.items(), key=lambda x: -x[1]))
    step = {"op": "RECALL", "text": f"{raw} memories from {len(queries)} queries in {ms} ms → {summary}", "detail": per_query}
    if backfilled:
        step["note"] = f"{', '.join(backfilled)} retained moments ago and still indexing in Hindsight; read from the write-through index."
    return list(recs.values()), step


def sections(a: dict) -> dict:
    m = a["main_belief"]
    top = a["coverage"]["ranked"][0] if a["coverage"]["ranked"] else None
    by_id = {e["experiment_id"]: e for e in a["experiments"]}
    believed = None
    if m:
        src = by_id.get(m["source"])
        believed = {"statement": m["statement"], "date": m["date"], "source": m["source"], "author": m.get("author"),
                    "source_result": src and {"lift": src["lift"], "conditions": src["conditions"], "name": src["name"]}}
    later = []
    if m:
        for i in m["later"]:
            e = by_id.get(i["id"])
            later.append({"type": "experiment", "id": i["id"], "date": i["date"], "lift": i["lift"], "agrees": i["agrees"], "name": e and e["name"]})
        for n in a["notes"]:
            if n["timestamp"][:10] > m["date"]:
                later.append({"type": "note", "id": n.get("observation_id") or n.get("note_id"), "date": n["timestamp"][:10], "text": n["note"],
                              "author": n.get("author"), "from_chat": n.get("source") == "chat"})
        later.sort(key=lambda x: x["date"])
    return {
        "believed": believed,
        "later": later,
        "now_know": engine.now_know(a),
        "unknown": top and {"label": top["label"], "why": top["why"], "cell": top["cell"]},
        "planned": [{"id": p.get("planned_experiment"), "note": p.get("note")} for p in a["planned"]],
    }


async def ask(question: str, use_memory: bool = True) -> dict:
    routed = await llm.route(question, COMPANY["topics"], STATE["last_topic"])
    topic = TOPICS[routed["topic"]]
    if not use_memory:
        return {"mode": "amnesia", "question": question, "route": routed, "topic": topic, "answer": await llm.amnesia(question)}
    STATE["last_topic"] = topic["id"]
    mem = get_memory()
    trace = [{"op": "RETAIN", "text": f"Question stored; routed as '{routed['type'].replace('_', ' ')}' about {topic['label'].lower()} ({routed['source']})"}]
    records, step = await gather(topic)
    trace.append(step)

    a = engine.analyze(topic, COMPANY, records)
    trace.append({"op": "COMPARE", "text": f"{a['counts']['clean']} clean comparisons, {a['counts']['confounded']} confounded, {a['counts']['set_aside']} set aside",
                  "detail": [f"{c['a']} vs {c['b']}: only {c['changes'][0]['label']} differs ({c['changes'][0]['from']} → {c['changes'][0]['to']}), "
                             f"{c['lift_a'] * 100:+.0f}% → {c['lift_b'] * 100:+.0f}%" for c in a["clean"]] + [f"Set aside {s['id']}: {s['reason']}" for s in a["set_aside"]]})
    m = a["main_belief"]
    if m:
        trace.append({"op": "REVISE", "text": f"“{m['statement']}” → {m['status_name']}",
                      "detail": [f"{h['date']}: {engine.STATUS_NAME[h['status']]} (after {h['by']})" for h in m["history"]] + [m["why"]]})
    cov = a["coverage"]
    top = cov["ranked"][0] if cov["ranked"] else None
    trace.append({"op": "COVERAGE", "text": f"{cov['counts']['tested']} tested, {cov['counts']['untested']} never tested" + (f", {cov['counts']['planned']} planned" if cov["counts"]["planned"] else "")
                  + (f"; top gap: {top['label']}" if top else ""), "detail": [f"{r['label']}: score {r['score']}. {r['why']}" for r in cov["ranked"]]})

    nk = engine.now_know(a)
    ctx = json.dumps({"computed": nk, "clean_comparisons": [f"{c['a']} vs {c['b']}" for c in a["clean"]]}, ensure_ascii=False)
    written, reflection, model = await asyncio.gather(
        llm.answer(question, a, routed["type"], nk),
        safe(mem.reflect(f"What did the team learn about {topic['label'].lower()} over time, and did later evidence change the original conclusion?", ctx,
                         tags=[f"area:{topic['area']}", "kind:belief"]), default=None, timeout=45),
        safe(mem.mental_model("current-beliefs"), default=None, timeout=15),
    )
    trace.append({"op": "ANSWER", "text": f"Evidence-backed answer written ({written['source']})" + ("; Hindsight reflection complete" if reflection else ""),
                  "detail": [reflection] if reflection else []})

    qa = {"qa_id": f"QA-{uuid.uuid4().hex[:6].upper()}", "kind": "qa", "timestamp": f"{COMPANY['today']}T{datetime.now().strftime('%H:%M:%S')}+05:30",
          "feature_area": topic["area"], "question": question, "answer": written["headline"] + ". " + nk}
    asyncio.create_task(safe(mem.retain([qa], wait=False), timeout=60))

    return {"mode": "memory", "memory_backend": mem.mode, "question": question, "route": routed, "topic": topic, "written": written,
            "sections": sections(a), "analysis": a, "trace": trace, "reflection": reflection, "mental_model": model}
