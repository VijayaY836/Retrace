# RETRACE build roadmap

Legend: ✅ done · 🟡 code done, needs your keys/machine · ⬜ to do

| # | Phase | Status | Where |
|---|---|---|---|
| 0 | Setup: Hindsight Cloud + MEMHACK99, Groq/OpenRouter key, OpenClaw + Hindsight plugin | ⬜ you | Section A below |
| 1 | Study self-driving-agents (Experiment Tracker, bank-template format) | ✅ | Format used in `retrace-agent/` |
| 2 | Project skeleton (reused ORIGIN's Hindsight wrapper, LLM fallbacks, theme, memory trace) | ✅ | `backend/app`, `frontend/` |
| 3 | NOVA dataset: 22 experiments + EXP-24 demo, 5 beliefs, observations, product changes, events | ✅ | `backend/data/nova/` |
| 4 | RETRACE agent package: bank template (missions, 4 directives, 2 mental models) + seed knowledge | ✅ validated against the Hindsight SDK schema | `retrace-agent/` |
| 5 | Shared memory: seed the bank, point OpenClaw at the same bank | 🟡 | Section B |
| 6 | Learning engine: clean comparisons, belief status + history, then vs now, coverage, next-test ranking | ✅ 11 tests pass | `backend/app/engine.py`, `backend/tests/` |
| 7 | Pipeline + API: router, RETAIN→RECALL→COMPARE→REVISE→COVERAGE→ANSWER, reflect, mental model, Amnesia Mode, add evidence/decision/note | ✅ | `backend/app/agent.py`, `main.py` |
| 8 | Frontend: Ask panel, Learning Timeline with belief lanes, Clean comparisons, Coverage map, four-part answer, memory trace | ✅ fits 1440×800 without scrolling | `frontend/src/` |
| 9 | Test with real Hindsight + Groq, tune recall, rehearse 5 clean runs | 🟡 | Section C |
| 10 | Submission: repo, demo video, content deliverables | ⬜ | Section D |

---

## A. Setup (Phase 0)

1. **Hindsight Cloud**: sign up at https://ui.hindsight.vectorize.io, create an API key (`hsk_…`), add promo code **MEMHACK99** in **Billing**.
2. **LLM**: Groq key at https://console.groq.com/keys (or OpenRouter).
3. **OpenClaw**: install OpenClaw (version 2026.7.x–2026.9.x works with plugin 0.12.0+), then:
   ```bash
   openclaw plugins install @vectorize-io/hindsight-openclaw
   npx --package @vectorize-io/hindsight-openclaw hindsight-openclaw-setup --mode cloud --token hsk_your_token
   ```
4. Join the Hindsight Community Slack for help.

## B. Shared memory (Phase 5)

```bash
cd backend
cp .env.example .env        # paste HINDSIGHT_API_KEY and GROQ_API_KEY
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py              # applies retrace-agent/bank-template.json, then loads NOVA's history
```
Wait 3–5 minutes. Then point OpenClaw at the **same** bank and turn on the knowledge tools:
```bash
openclaw config set plugins.entries.hindsight-openclaw.config.dynamicBankId false
openclaw config set plugins.entries.hindsight-openclaw.config.bankId retrace-nova
openclaw config set plugins.entries.hindsight-openclaw.config.enableKnowledgeTools true
npx @vectorize-io/self-driving-agents install ./retrace-agent --harness openclaw
openclaw gateway
```
✅ Check: chat "We now think the 7-step flow, not the badges, was the real problem in EXP-07" in OpenClaw. A few minutes later, ask the dashboard "Was our original conclusion about gamification wrong?". The note appears under **What we later saw** with a **from chat** tag.

## C. Test and rehearse (Phase 9)

- [ ] Header shows **Hindsight memory connected**
- [ ] Click RECALL in the memory trace: every query returns memories
- [ ] Gamification belief shows **Revised**; dark mode **Held up**; annual plan **Weak basis**
- [ ] Coverage top gap: **gamified + 3 steps + new users + iOS**
- [ ] Add EXP-24 → push belief goes **Challenged → Revised** on the timeline
- [ ] Record decision → EXP-25 shows as **planned**, next gap changes
- [ ] Amnesia Mode gives generic advice
- [ ] Turn off the LLM key: answers still work (fallbacks)
- [ ] **Reset demo** between runs; 5 clean runs in a row

## D. Submission (Phase 10)

- [ ] Push to GitHub (keys are git-ignored)
- [ ] Demo video under 3 minutes (script in `docs/spec.md`, section 13)
- [ ] Live demo rehearsed, backup recording ready
- [ ] Every team member: article, social post, video (Hackathon Content Guide)
