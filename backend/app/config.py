"""Settings and NOVA data."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
load_dotenv(ROOT / ".env")

DATA = ROOT / "data" / "nova"
LEDGER_PATH = ROOT / "data" / "ledger.json"
AGENT_DIR = REPO / "retrace-agent"

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "").strip()
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "qwen/qwen3-32b").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b").strip()
OPENROUTER_FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "qwen/qwen3-32b").strip()
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").strip()

COMPANY = json.loads((DATA / "company.json").read_text(encoding="utf-8"))
DEMO = json.loads((DATA / "demo.json").read_text(encoding="utf-8"))
BANK_ID = os.getenv("RETRACE_BANK_ID", "").strip() or COMPANY["bank_id"]
TOPICS = {t["id"]: t for t in COMPANY["topics"]}
SOURCE_TAG = "src:retrace"  # marks memories written by RETRACE (vs. captured from OpenClaw chat)


def seed_records() -> list[dict]:
    out = []
    for f in ["experiments", "beliefs", "observations", "product_state", "events"]:
        out += json.loads((DATA / f"{f}.json").read_text(encoding="utf-8"))
    return out
