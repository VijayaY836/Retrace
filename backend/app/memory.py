"""Hindsight memory layer for RETRACE (one bank shared with the OpenClaw chat agent).

LocalMemory exists only so the app can start before you add a key; the UI shows a
loud warning in that mode.
"""
import asyncio
import hashlib
import json
import logging
import re

from . import ledger
from .config import AGENT_DIR, BANK_ID, HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL, SOURCE_TAG
from .records import narrative, record_id, tags_for, to_memory_item

log = logging.getLogger("retrace.memory")


def chat_note(res) -> dict | None:
    """A memory captured by the OpenClaw plugin (not written by RETRACE) becomes a 'team note from chat'."""
    if (res.type or "") == "observation":
        return None
    when = res.occurred_start or res.mentioned_at
    ts = when.isoformat() if hasattr(when, "isoformat") else (str(when) if when else "2026-09-28T12:00:00+05:30")
    return {"note_id": "CHAT-" + hashlib.sha1(res.text.encode()).hexdigest()[:8], "kind": "note", "source": "chat",
            "timestamp": ts, "author": "Team chat (OpenClaw)", "feature_area": None, "note": res.text}


class HindsightMemory:
    mode = "hindsight"

    def __init__(self):
        from hindsight_client import Hindsight

        self.client = Hindsight(base_url=HINDSIGHT_BASE_URL, api_key=HINDSIGHT_API_KEY, timeout=120.0)

    async def apply_template(self) -> str:
        """Create/update the bank from retrace-agent/bank-template.json (missions, directives, mental models)."""
        from hindsight_client_api.api.bank_templates_api import BankTemplatesApi
        from hindsight_client_api.models import BankTemplateManifest

        manifest = BankTemplateManifest.from_dict(json.loads((AGENT_DIR / "bank-template.json").read_text(encoding="utf-8")))
        await BankTemplatesApi(self.client._api_client).import_bank_template(BANK_ID, manifest)
        return "template applied"

    async def retain(self, records: list[dict], wait: bool = True):
        items = [to_memory_item(r) for r in records]
        for i in range(0, len(items), 8):
            await self.client.aretain_batch(BANK_ID, items[i : i + 8], retain_async=not wait)

    async def recall(self, query: str, tags: list[str] | None = None, budget: str = "mid", max_tokens: int = 4096) -> list[dict]:
        kw = dict(query=query, budget=budget, max_tokens=max_tokens)
        if tags:
            kw.update(tags=tags, tags_match="any")
        resp = await self.client.arecall(BANK_ID, **kw)
        hits = []
        for res in resp.results or []:
            meta = res.metadata or {}
            rec = None
            if meta.get("record_json"):
                try:
                    rec = json.loads(meta["record_json"])
                except Exception:
                    rec = None
            doc = res.document_id or meta.get("record_id")
            if rec is None and doc:
                rec = ledger.get(doc)
            if rec is None and SOURCE_TAG not in (res.tags or []):
                rec = chat_note(res)
            hits.append({"document_id": doc, "text": res.text, "record": rec})
        return hits

    async def reflect(self, query: str, context: str, tags: list[str] | None = None) -> str | None:
        kw = dict(query=query, context=context, budget="low", max_tokens=700)
        if tags:
            kw.update(tags=tags, tags_match="any")
        resp = await self.client.areflect(BANK_ID, **kw)
        return (resp.text or "").strip() or None

    async def mental_model(self, model_id: str) -> dict | None:
        m = await self.client.aget_mental_model(BANK_ID, model_id, detail="content")
        hist = await self.client.aget_mental_model_history(BANK_ID, model_id)
        return {"id": model_id, "name": m.name, "content": m.content, "last_refreshed_at": str(m.last_refreshed_at or ""),
                "versions": len(hist or [])}

    async def delete(self, doc_ids: list[str]):
        for d in doc_ids:
            try:
                await self.client.documents.delete_document(BANK_ID, d)
            except Exception as e:
                log.info("delete %s: %s", d, str(e)[:120])

    async def delete_bank(self):
        try:
            await self.client.adelete_bank(BANK_ID)
        except Exception as e:
            log.info("delete_bank: %s", str(e)[:120])

    async def close(self):
        try:
            await self.client.aclose()
        except Exception:
            pass


class LocalMemory:
    mode = "local"

    async def apply_template(self):
        return "local"

    async def retain(self, records, wait=True):
        pass

    async def recall(self, query, tags=None, budget="mid", max_tokens=4096):
        words = {w for w in re.findall(r"[a-z0-9\-]+", query.lower()) if len(w) > 2}
        out = []
        for r in ledger.all_records():
            if tags and not set(tags) & set(tags_for(r)):
                continue
            t = narrative(r)
            s = sum(1 for w in words if w in t.lower())
            if s or tags:
                out.append((s, r, t))
        out.sort(key=lambda x: -x[0])
        return [{"document_id": record_id(r), "text": t, "record": r} for _, r, t in out[: max(12, max_tokens // 150)]]

    async def reflect(self, query, context, tags=None):
        return None

    async def mental_model(self, model_id):
        return None

    async def delete(self, ids):
        pass

    async def delete_bank(self):
        pass

    async def close(self):
        pass


_mem = None


def get_memory():
    global _mem
    if _mem is None:
        _mem = HindsightMemory() if HINDSIGHT_API_KEY else LocalMemory()
    return _mem


async def safe(coro, default=None, timeout=60.0):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except Exception as e:
        log.warning("memory call failed: %s", str(e)[:200])
        return default
