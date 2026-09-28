"""Create the RETRACE bank from retrace-agent/bank-template.json and load NOVA's history.

    python seed.py          # apply template + seed
    python seed.py --fresh  # delete the bank first
"""
import asyncio
import sys

from app import ledger
from app.config import BANK_ID, HINDSIGHT_API_KEY, seed_records
from app.memory import get_memory


async def main():
    if not HINDSIGHT_API_KEY:
        sys.exit("HINDSIGHT_API_KEY is empty in backend/.env. Add it first.")
    mem = get_memory()
    if "--fresh" in sys.argv:
        print(f"Deleting bank {BANK_ID} …")
        await mem.delete_bank()
    print(f"Applying retrace-agent/bank-template.json to bank '{BANK_ID}' (missions, directives, mental models) …")
    try:
        print(" ", await mem.apply_template())
    except Exception as e:
        print("  template import failed:", str(e)[:300])
    recs = seed_records()
    print(f"Retaining {len(recs)} NOVA records …")
    for i in range(0, len(recs), 8):
        await mem.retain(recs[i : i + 8], wait=False)
        print(f"  queued {min(i + 8, len(recs))}/{len(recs)}")
    ledger.reset()
    await mem.close()
    print("\nDone. Hindsight is extracting facts in the background: wait 3–5 minutes before the demo.")


if __name__ == "__main__":
    asyncio.run(main())
