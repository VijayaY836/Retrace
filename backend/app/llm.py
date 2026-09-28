"""LLM calls (Groq or OpenRouter) with retries, JSON validation and deterministic fallbacks."""
import asyncio
import json
import logging
import re

from .config import (GROQ_API_KEY, GROQ_FALLBACK_MODEL, GROQ_MODEL, LLM_PROVIDER, OPENROUTER_API_KEY,
                     OPENROUTER_FALLBACK_MODEL, OPENROUTER_MODEL)

log = logging.getLogger("origin.llm")
_client = None


USE_OPENROUTER = LLM_PROVIDER == "openrouter"
MODEL = OPENROUTER_MODEL if USE_OPENROUTER else GROQ_MODEL
FALLBACK_MODEL = OPENROUTER_FALLBACK_MODEL if USE_OPENROUTER else GROQ_FALLBACK_MODEL


def enabled() -> bool:
    return bool(OPENROUTER_API_KEY if USE_OPENROUTER else GROQ_API_KEY)


def provider() -> str:
    return "openrouter" if USE_OPENROUTER else "groq"


def _get():
    global _client
    if _client is None:
        if USE_OPENROUTER:
            from openai import AsyncOpenAI  # OpenRouter speaks the OpenAI API

            _client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1",
                                  max_retries=1, timeout=30.0,
                                  default_headers={"X-Title": "RETRACE - HackwithHyderabad 3.0"})
        else:
            from groq import AsyncGroq

            _client = AsyncGroq(api_key=GROQ_API_KEY, max_retries=1, timeout=30.0)
    return _client


def _parse(text: str) -> dict | None:
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def chat_json(system: str, user: str, required: list[str]) -> dict | None:
    if not enabled():
        return None
    attempts = [(MODEL, True), (MODEL, False), (FALLBACK_MODEL, False)]
    for model, json_mode in attempts:
        try:
            kwargs = dict(
                model=model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.2,
                max_tokens=2000,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = await asyncio.wait_for(_get().chat.completions.create(**kwargs), timeout=35)
            data = _parse(resp.choices[0].message.content or "")
            if data and all(k in data for k in required):
                return data
            log.warning("LLM output missing keys from %s", model)
        except Exception as e:
            log.warning("LLM call failed (%s, json=%s): %s", model, json_mode, str(e)[:200])
    return None


# ---------------- question router ----------------
QTYPES = ["what_happened", "why_failed", "was_right", "still_applies", "what_next", "should_we"]
QTYPE_RULES = [
    ("what_next", ["test next", "what next", "haven't tested", "havent tested", "never tested", "untested", "what should we test"]),
    ("still_applies", ["still apply", "still true", "still hold", "today", "still valid", "apply now"]),
    ("was_right", ["wrong", "right", "correct", "was our", "conclusion"]),
    ("why_failed", ["why did", "why was", "why "]),
    ("should_we", ["should we", "bring back", "bring it back", "try again", "revive"]),
    ("what_happened", ["what happened", "what did we", "did we", "tried", "tested", "test"]),
]


def route_keywords(question: str, topics: list[dict], last_topic: str | None = None) -> dict:
    q = question.lower()
    qtype = next((t for t, kws in QTYPE_RULES if any(k in q for k in kws)), "should_we")
    topic = next((t["id"] for t in topics if any(k in q for k in t["keywords"])), None) or last_topic or topics[0]["id"]
    return {"type": qtype, "topic": topic, "source": "keywords"}


async def route(question: str, topics: list[dict], last_topic: str | None = None) -> dict:
    fallback = route_keywords(question, topics, last_topic)
    system = ("Classify a product manager's question about past experiments. "
              f"type must be one of {QTYPES}. topic must be one of {[t['id'] for t in topics]} "
              f"(topics: {[(t['id'], t['label']) for t in topics]}). If the question continues an earlier topic, use '{last_topic}'. "
              'Respond ONLY with JSON: {"type": str, "topic": str}')
    data = await chat_json(system, question, ["type", "topic"])
    if data and data.get("type") in QTYPES and data.get("topic") in {t["id"] for t in topics}:
        return {"type": data["type"], "topic": data["topic"], "source": "llm"}
    return fallback


# ---------------- Amnesia Mode ----------------
async def amnesia(question: str) -> dict:
    system = ("You are a helpful product and growth advisor. You have NO access to this company's experiment history. "
              'Answer briefly. Respond ONLY with JSON: {"answer": str, "suggestions": [str]} (2-3 suggestions).')
    data = await chat_json(system, question, ["answer", "suggestions"])
    if data and isinstance(data.get("suggestions"), list):
        return {**data, "source": "llm"}
    return {"answer": "It can work when implemented thoughtfully. Many apps see engagement gains, but results vary by audience, so keep it simple and measure carefully.",
            "suggestions": ["Run an A/B test with a clear success metric", "Start with a small segment", "Watch for novelty effects"], "source": "fallback"}


# ---------------- answer writer ----------------
def _facts(a: dict, qtype: str) -> dict:
    m = a["main_belief"]
    top = a["coverage"]["ranked"][0] if a["coverage"]["ranked"] else None
    return {
        "question_type": qtype,
        "belief": m and {k: m[k] for k in ("statement", "date", "source", "status_name", "why")},
        "later_evidence": m and [{"id": i["id"], "lift": i["lift"], "agrees_with_belief": i["agrees"]} for i in m["later"]],
        "clean_comparisons": [{"pair": f"{c['a']} vs {c['b']}", "only_difference": c["changes"][0], "lift_before": c["lift_a"], "lift_after": c["lift_b"]} for c in a["clean"][:6]],
        "set_aside": [{"id": s["id"], "reason": s["reason"]} for s in a["set_aside"]],
        "then_vs_now": a["then_vs_now"] and a["then_vs_now"]["verdict"],
        "top_untested": top and {"combination": top["label"], "why": top["why"]},
        "planned": [p.get("note") for p in a["planned"]],
    }


PHRASE = {"held_up": "has held up", "challenged": "has been challenged", "revised": "needs revising", "weak_basis": "rests on weak evidence", "untested_since": "hasn't been tested since"}


def fallback_answer(a: dict, qtype: str, now_know: str) -> dict:
    m = a["main_belief"]
    top = a["coverage"]["ranked"][0] if a["coverage"]["ranked"] else None
    exps = a["experiments"]
    tested = ", ".join(f"{e['experiment_id']} ({e['lift'] * 100:+.0f}%)" for e in exps if e["quality"]["level"] == "ok")
    if not m:
        return {"headline": f"No recorded belief about {a['topic']['label'].lower()} yet", "answer": f"Experiments in {a['area_label'].lower()}: {tested or 'none'}."}
    gap = f" The most informative untested combination is {top['label']}." if top else ""
    planned = f" Already planned: {a['planned'][0]['note']}" if a["planned"] else ""
    by_type = {
        "what_happened": (f"{a['topic']['label']}: {len(exps)} experiments in memory", f"Tested: {tested}. The team concluded “{m['statement']}” after {m['source']}."),
        "why_failed": (f"Why the team concluded “{m['statement']}”", f"After {m['source']} ({m['date'][:7]}), the team wrote: “{m['statement']}” Later evidence: {m['why']}"),
        "was_right": (f"The original conclusion {PHRASE[m['status']]}", now_know),
        "still_applies": ("Does the old result still apply?", (a["then_vs_now"] or {}).get("verdict", "No comparable conditions found.")),
        "what_next": (f"Next test: {top['label']}" if top else "No untested combinations left", (top["why"] if top else "") + planned),
        "should_we": (f"Worth another look: the old conclusion {PHRASE[m['status']]}" if m["status"] in ("revised", "weak_basis", "challenged") else f"The old conclusion {PHRASE[m['status']]}", now_know + gap + planned),
    }
    h, t = by_type.get(qtype, by_type["should_we"])
    return {"headline": h, "answer": t}


async def answer(question: str, a: dict, qtype: str, now_know: str) -> dict:
    system = ("You are RETRACE, the memory of a product team's experiments. Answer the question using ONLY the computed facts given. "
              "Rules: cite experiment IDs; never invent IDs, numbers or dates; never claim causation (say 'the evidence suggests'); "
              "present untested combinations as open questions, never as predictions; never blame people. Plain, direct English, 2-4 sentences. "
              'Respond ONLY with JSON: {"headline": str (max 12 words), "answer": str}')
    user = json.dumps({"question": question, "facts": _facts(a, qtype), "summary": now_know}, ensure_ascii=False)
    data = await chat_json(system, user, ["headline", "answer"])
    allowed = {e["experiment_id"] for e in a["experiments"]} | {s["id"] for s in a["set_aside"]} | {p.get("planned_experiment") for p in a["planned"]}
    if data:
        cited = set(re.findall(r"EXP-\d+", data["headline"] + " " + data["answer"]))
        if cited <= allowed:
            return {**data, "source": "llm"}
        log.warning("LLM cited unknown experiments %s; using fallback", cited - allowed)
    return {**fallback_answer(a, qtype, now_know), "source": "fallback"}
