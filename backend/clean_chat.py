"""Remove anything from the RETRACE bank that isn't NOVA's own seed data or the agent's knowledge
files. This catches BOTH kinds of OpenClaw-saved content we've seen: the automatic transcript save
(document ids like "openclaw:agent:...") and the explicit agent_knowledge_ingest tool call (document
ids like "note-exp07-revision", or whatever title the agent chose).

    python clean_chat.py          # dry run: lists what would be deleted
    python clean_chat.py --yes    # delete them

Safe by construction: it only ever compares against the known-good id list (NOVA's real records
and the agent's seed knowledge files) and deletes everything else. It can never touch a real
experiment or belief, because those ids are always in the known-good set.
"""
import asyncio
import sys

from app.config import AGENT_DIR, BANK_ID, HINDSIGHT_API_KEY, seed_records
from app.memory import get_memory
from app.records import record_id


async def main():
    if not HINDSIGHT_API_KEY:
        sys.exit("HINDSIGHT_API_KEY is empty in backend/.env")

    known = {record_id(r) for r in seed_records()}
    agent_docs = {p.stem for p in AGENT_DIR.glob("*.md")}
    safe = known | agent_docs

    mem = get_memory()
    docs, offset = [], 0
    while True:
        page = await mem.client.documents.list_documents(BANK_ID, limit=100, offset=offset)
        docs += [d.id for d in page.items]
        offset += 100
        if offset >= page.total:
            break

    extra = [d for d in docs if d not in safe]
    print(f"{len(docs)} documents in '{BANK_ID}', {len(extra)} are NOT part of NOVA's seed data or the agent's knowledge files:")
    for d in extra:
        print("  ", d)

    if extra and "--yes" in sys.argv:
        for d in extra:
            await mem.client.documents.delete_document(BANK_ID, d)
        print(f"Deleted {len(extra)}.")
    elif extra:
        print("\nDry run only. Re-run with --yes to delete them.")
    else:
        print("\nNothing to delete — the bank only contains NOVA's seed data and agent knowledge.")
    await mem.close()


if __name__ == "__main__":
    asyncio.run(main())