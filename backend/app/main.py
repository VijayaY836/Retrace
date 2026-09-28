"""RETRACE API."""
import logging
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import agent, ledger, llm
from .config import BANK_ID, COMPANY, DEMO, FRONTEND_ORIGIN, TOPICS
from .memory import get_memory, safe
from .records import narrative, record_id

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("retrace")
app = FastAPI(title="RETRACE — the memory of your experiments")
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])

SUGGESTED = [
    {"type": "should_we", "text": "Should we bring gamified onboarding back?"},
    {"type": "was_right", "text": "Was our original conclusion about gamification wrong?"},
    {"type": "still_applies", "text": "Would EXP-07's failure still apply today?"},
    {"type": "what_next", "text": "What should we test next for gamified onboarding?"},
    {"type": "was_right", "text": "Do push notifications hurt retention?"},
    {"type": "what_happened", "text": "What did we learn about dark mode?"},
]


@app.on_event("startup")
async def startup():
    if not ledger.LEDGER_PATH.exists():
        ledger.reset()
    if get_memory().mode == "local":
        log.warning("HINDSIGHT_API_KEY not set: running on LOCAL fallback memory.")


async def retain(recs, wait=True):
    return await safe(get_memory().retain(recs, wait=wait), default="fail", timeout=120)


@app.get("/health")
async def health():
    return {"memory_backend": get_memory().mode, "bank_id": BANK_ID, "llm": llm.provider() if llm.enabled() else "fallback"}


@app.get("/company")
async def company():
    return {**COMPANY, "suggested": SUGGESTED}


@app.get("/memory")
async def memory():
    items = sorted(ledger.all_records(), key=lambda r: r["timestamp"], reverse=True)
    return [{"id": record_id(r), "kind": r["kind"], "timestamp": r["timestamp"], "text": narrative(r)} for r in items]


class Ask(BaseModel):
    question: str = Field(min_length=3)
    memory: bool = True


@app.post("/ask")
async def ask(body: Ask):
    return await agent.ask(body.question.strip(), use_memory=body.memory)


@app.post("/evidence/demo")
async def add_demo_result():
    """EXP-24 finishes: two pushes a day on Android."""
    r = DEMO["new_result"]
    ledger.upsert(r)
    await retain([r])
    return r


class Note(BaseModel):
    text: str = Field(min_length=3)
    topic: str | None = None
    author: str = "Product team"


@app.post("/evidence/note")
async def add_note(body: Note):
    t = TOPICS.get(body.topic or "") or TOPICS[agent.STATE["last_topic"] or "gamification"]
    r = {"note_id": f"NOTE-{uuid.uuid4().hex[:5].upper()}", "kind": "note", "source": "dashboard", "timestamp": f"{COMPANY['today']}T15:00:00+05:30",
         "author": body.author, "feature_area": t["area"], "note": body.text}
    ledger.upsert(r)
    await retain([r])
    return r


@app.post("/decision/demo")
async def add_demo_decision():
    """The team decides to run the suggested iOS test as EXP-25."""
    r = DEMO["decision"]
    ledger.upsert(r)
    await retain([r])
    return r


@app.get("/mental-model")
async def mental_model():
    return await safe(get_memory().mental_model("current-beliefs"), default=None, timeout=15)


@app.post("/demo/reset")
async def reset():
    ids = ledger.demo_ids()
    await safe(get_memory().delete(ids), timeout=60)
    ledger.reset()
    agent.STATE["last_topic"] = None
    return {"reset": True, "removed": ids}
