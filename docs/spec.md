# RETRACE — The R&D Agent That Remembers What Your Company Already Learned

> **Companies don't lack data. Their experiments just never add up to knowledge.**

Build a polished, hackathon-ready web application called **RETRACE** for **HackwithHyderabad 3.0: AI Agents That Learn Using Hindsight**.

---

## 1. One-Line Pitch

RETRACE is a memory for a product team's experiments. It remembers not just what was tested and what happened, but **the conditions, what the team concluded, and how later evidence changed that conclusion**. So when someone asks "should we try this again?", RETRACE tells them what the past actually taught them, and what has never been tested.

---

## 2. The Problem

Product teams run experiments constantly: onboarding changes, pricing tests, notification strategies, UI variants, recommendation logic.

Months later, someone proposes something similar. The organization remembers:

> "We tried that. It didn't work."

But not:

> "We tried that **under these conditions**, we **concluded** it failed for this reason, and **later evidence** showed the conclusion was too broad."

Two expensive mistakes follow:
1. **Repeating** an experiment that already has a clear answer.
2. **Rejecting** a good idea because it failed once under completely different conditions.

Experimentation tools (Statsig, Eppo, Optimizely) store **results**. Nobody tracks how the team's **interpretation** of those results changed over time, which comparisons are actually valid, or which combinations were **never tested**. That is the gap RETRACE fills.

**Buyer:** Heads of Product, Growth and Data at consumer apps that run 50+ experiments a year.

---

## 3. Core Principles

1. **Memory drives the intelligence.** RETRACE must be visibly better *because* it remembers. Without memory, it gives generic advice.
2. **Track beliefs, not just results.** Every team conclusion is stored as its own dated memory, so RETRACE can show how beliefs evolved.
3. **Only honest comparisons.** RETRACE never claims cause and effect. It separates clean comparisons (one thing changed) from messy ones (many things changed).
4. **Not every old conclusion is wrong.** RETRACE must also say "this belief has held up," or it looks like it just contradicts everything.
5. **Suggest questions, not guarantees.** Next-experiment suggestions are phrased as "this would test an unresolved question," never "this will work."
6. **Real learning, not staged learning.** The agent recalls everything relevant from the start. It improves when **new evidence is added**, not by pretending to forget.

---

## 4. The Five Questions RETRACE Answers

| # | Question | Example | How it's answered |
|---|---|---|---|
| A | What did we try? | "What happened when we tested gamified onboarding?" | Recall all related experiments and their conditions |
| B | Why did we think it failed? | "Why did EXP-07 fail?" | Recall the team's original interpretation, with its date |
| C | Was that conclusion right? | "Was our original conclusion wrong?" | Compare later evidence against the belief; use clean comparisons |
| D | Does the old result still apply? | "Would EXP-07's failure still apply today?" | Check whether today's conditions match the old ones |
| E | What haven't we tested? | "What should we test next?" | Calculate which condition combinations were never tried |

A question router classifies each question into A–E (LLM with function calling, validated; keyword fallback if the call fails).

---

## 5. Hero Feature: Clean Comparisons ("Minimal Pairs")

Most experiments change several things at once. So RETRACE looks for **pairs of experiments that differ in exactly one condition**. Only these pairs isolate the effect of that one condition.

Example:

| | EXP-07 | EXP-13 |
|---|---|---|
| Gamification | ✅ | ✅ |
| Onboarding steps | **7** | **3** |
| Segment | New users | New users |
| Platform | Android | Android |
| Plan | ₹299 | ₹299 |
| Activation lift | **−14%** | **+11%** |

RETRACE says:

> "EXP-07 vs EXP-13 is the cleanest comparison available: the only difference was 7-step vs 3-step onboarding. That is strong evidence onboarding length, not gamification, drove the drop."

And for a messy comparison:

> "EXP-21 also shows gamification working (+18%), but it changed segment, platform and price at the same time. It supports the pattern but cannot isolate it."

Every comparison in the UI is labelled **Clean (1 difference)** or **Confounded (N differences)**.

---

## 6. Belief Tracking

Every team conclusion is stored as a separate, dated **belief** memory. Each belief has a status that RETRACE recalculates as evidence arrives:

| Status | Meaning | Visual |
|---|---|---|
| **Held up** | Later evidence agrees with it | Green |
| **Challenged** | Some later evidence disagrees | Amber |
| **Revised** | A clean comparison contradicts it; a narrower belief replaces it | Red strikethrough → new belief |
| **Untested since** | No later evidence either way | Grey |

RETRACE's answer always follows this structure:

- **What we believed:** "Gamification reduces activation." (EXP-07, Mar 2024)
- **What we later observed:** "Results turned positive when onboarding was shorter." (EXP-13, EXP-21)
- **What we now know:** "The original conclusion likely mixed up gamification with onboarding length."
- **What remains unknown:** "Gamification + 3-step onboarding + new iOS users has never been tested."

---

## 7. Coverage Map (What Haven't We Tested?)

For any feature, RETRACE builds a grid of the conditions that matter (for example gamification × onboarding length × segment × platform) and marks each cell:

- ✅ Tested (with result)
- ⚠️ Tested, but inconclusive (sample too small)
- ❌ Never tested

**Next-experiment ranking (deterministic):** an untested cell scores higher when it:
1. is one condition away from tested cells that **disagree** with each other (it resolves a conflict), and
2. tests a condition level that has **never been tried at all** (for example: iOS new users).

Output:

> **Potentially informative next experiment:** Gamification + 3-step onboarding + new users + iOS.
> **Why:** It is one step away from EXP-13 (Android, +11%) and would show whether the result holds on iOS. New iOS users have never been in a gamification test.

---

## 8. The Learning Loop (Real, Not Staged)

RETRACE gets smarter when **new evidence enters memory**:

1. **Add a result:** the PM adds EXP-24's result (just finished). RETRACE retains it, and belief statuses update live. Example: "Push notifications hurt retention" moves from **Challenged** to **Revised**.
2. **Add an interpretation:** a PM note ("We think the 7-step flow was the real problem in EXP-07") is retained as a dated belief and appears on the timeline.
3. **Record a decision:** "We'll run the suggested iOS test as EXP-25." RETRACE remembers it. Next time someone asks "what should we test next?", it says: "EXP-25 is already planned for that. The next most informative gap is…"

The demo must show at least one of these changing RETRACE's answer on screen.

---

## 9. Amnesia Mode (Before/After Proof)

Toggle: **Memory ON / Amnesia Mode**.

- **Amnesia:** the same LLM, no Hindsight recall. It gives generic advice ("gamification can improve engagement when implemented thoughtfully…").
- **Memory ON:** the full RETRACE answer with experiment IDs, clean comparisons, belief history and the untested gap.

---

## 10. Demo Dataset: NOVA

### The Company

**NOVA**, a fictional Bengaluru consumer subscription app for learning skills in short daily lessons. It has 2.3M users on Android and iOS, three plans (₹299, ₹499, ₹999/year), and has run product experiments for two years (Jan 2024 to Sep 2026).

### Condition Fields (every experiment uses these)

```json
{
  "experiment_id": "EXP-07",
  "name": "Gamified onboarding v1",
  "date_start": "2024-03-04",
  "date_end": "2024-03-25",
  "owner": "Riya Menon (Growth PM)",
  "hypothesis": "Gamified onboarding increases activation",
  "feature_area": "onboarding",
  "conditions": {
    "gamification": true,
    "onboarding_steps": 7,
    "segment": "new_users",
    "platform": "android",
    "plan_price": 299,
    "notif_per_day": null
  },
  "primary_metric": "activation_rate",
  "control_rate": 0.412,
  "variant_rate": 0.354,
  "lift": -0.14,
  "sample_size": 48200,
  "p_value": 0.003,
  "team_interpretation": "Gamification hurts onboarding. Users found badges distracting.",
  "decision": "Shelved gamification"
}
```

### Hidden Pattern 1 (hero): Gamified onboarding

| ID | Date | Gamif. | Steps | Segment | Platform | Plan | Lift | Team conclusion at the time |
|---|---|---|---|---|---|---|---|---|
| EXP-04 | Jan 2024 | ❌ | 7 | New | Android | ₹299 | −9% | "New onboarding copy didn't help" |
| EXP-07 | Mar 2024 | ✅ | 7 | New | Android | ₹299 | **−14%** | **"Gamification hurts onboarding"** |
| EXP-10 | Jul 2024 | ❌ | 3 | New | Android | ₹299 | +6% | "Shorter onboarding helps a little" |
| EXP-13 | Nov 2024 | ✅ | 3 | New | Android | ₹299 | **+11%** | "Short onboarding works" (gamification not mentioned) |
| EXP-21 | Aug 2025 | ✅ | 3 | Existing | iOS | ₹499 | +18% | "Gamified refresher works for existing users" |

**The clean comparisons RETRACE should find:**
- EXP-07 vs EXP-13: only onboarding steps differ (7 → 3), lift −14% → +11%
- EXP-04 vs EXP-07: only gamification differs (with 7 steps), −9% → −14%
- EXP-10 vs EXP-13: only gamification differs (with 3 steps), +6% → +11%
- EXP-04 vs EXP-10: only steps differ (no gamification), −9% → +6%

**The true story:** 7-step onboarding hurts activation with or without gamification. With short onboarding, gamification *adds* about 5 points. The belief "gamification hurts onboarding" is **Revised**.

**The gap:** new users on **iOS** have never been in any onboarding test with gamification.

### Hidden Pattern 2 (supporting): Push notifications

- EXP-09 (Jun 2024): 5 pushes/day → 30-day retention −8%. Belief: **"Push notifications hurt retention."**
- EXP-16 (Mar 2025): 1 push/day, same segment → +4%. Belief becomes **Challenged**.
- **EXP-24 (Sep 2026, added live during the demo):** 2 pushes/day → +3%. The belief becomes **Revised** to "High push frequency hurts retention; 1–2/day helps." This is the learning-loop moment.

### Hidden Pattern 3 (control): A belief that held up

- EXP-06 (Feb 2024): Dark mode default → no retention change (+0.3%, p = 0.71). Belief: **"Dark mode doesn't move retention."**
- EXP-18 (May 2025): Dark mode on iOS → +0.1%, p = 0.84. Status: **Held up.**

This proves RETRACE doesn't reflexively overturn every old conclusion.

### Decoys (RETRACE must handle these correctly)

- **Decoy A: Underpowered test.** EXP-15 (₹999 annual plan banner, n = 780, p = 0.41) showed −12%. The team concluded "annual plans scare users." RETRACE flags it: "**Inconclusive**: sample too small to support any conclusion."
- **Decoy B: External event.** EXP-19 (new paywall, Oct 2025) ran during a 6-hour app store outage and the Diwali sale. RETRACE marks it: "Results overlap with an outage and a sale; treat with caution." It is stored as a separate **external event** memory.
- **Decoy C: Same word, different thing.** EXP-22 "Gamified referral leaderboard" (referrals, not onboarding). RETRACE must not mix it into onboarding answers: "Different feature area (referrals)."

### Background Noise

About 12 more experiments across pricing, recommendations, lesson length, streak reminders, UI and checkout, so the history feels like two real years (**25–28 experiments total**).

### Supporting Memories

- **Later observations:** for example a user-research note (Jan 2025): "Interviewed 14 churned new users; 9 mentioned the onboarding being 'too long'."
- **External events:** outages, festival sales, an iOS release.
- **Team notes:** for example "Riya moved to Payments team in Jun 2025," so knowledge loss is part of the story.

---

## 11. Hindsight Integration (Central, Not Decorative)

One memory bank: `retrace-nova`. Check the Hindsight docs for exact SDK signatures before implementing.

### What Gets Retained (each as its own memory)

| Memory type | Why it's separate |
|---|---|
| Experiment (design + conditions + result) | The facts of what happened |
| Team interpretation / belief (dated) | So beliefs can be tracked and revised over time |
| Later observation (research, support, analytics) | Evidence that arrives after the experiment |
| External event (outage, sale, OS release) | To flag contaminated results |
| Decision (shelved, shipped, planned next test) | So RETRACE knows what's already planned |
| Q&A outcome (what RETRACE concluded and when) | So its own past answers are part of the history |

Each memory carries its real timestamp, tags (`feature:onboarding`, `kind:belief`, `segment:new_users`, `platform:ios`), a `document_id`, and the structured record in metadata.

### How the Operations Map

| Hindsight | RETRACE use |
|---|---|
| **Retain** | Every experiment, belief, observation, event, decision, and new evidence added during the demo |
| **Recall** | Per question: related experiments, beliefs about them, later evidence, events overlapping their dates, planned decisions |
| **Reflect** | Synthesizes the "what we believed / observed / now know" narrative, with a reflect mission that forbids causal claims and requires citing experiment IDs |

### Hybrid Engine (Trustworthy, Not LLM Magic)

1. **Recall** from Hindsight.
2. **Deterministic learning engine** in code:
   - normalize experiment conditions
   - find clean comparisons (exactly one differing condition, same metric)
   - flag weak evidence (sample size under 2,000 or p-value ≥ 0.05 → inconclusive; overlapping external event → caution)
   - recalculate belief status from evidence dates and effect directions
   - build the coverage grid and rank untested cells
3. **LLM** (Groq or OpenRouter) writes the answer from those computed facts. It must not invent experiment IDs, numbers or dates, and it must use the grade-appropriate wording.

### Memory Trace Panel

```
RETAIN    Question stored
   ↓
RECALL    14 memories → 5 experiments, 3 beliefs, 1 research note
   ↓
COMPARE   4 clean comparisons found (EXP-07 vs 13, 04 vs 07, 10 vs 13, 04 vs 10)
   ↓
REVISE    Belief "Gamification hurts onboarding" → Revised
   ↓
COVERAGE  3 untested combinations; top gap: new users + iOS
   ↓
ANSWER    Evidence-backed summary with experiment IDs
```

---

## 12. UI / UX

Same design language as ORIGIN: light, colorful and professional, everything on one screen, and every color with a meaning.

### Layout

```
┌───────────────────────────────────────────────────────────────────────┐
│ RETRACE   NOVA                            [ Memory ON | Amnesia ]     │
├───────────────┬───────────────────────────────────┬───────────────────┤
│ ASK RETRACE   │ LEARNING TIMELINE                 │ WHAT WE LEARNED   │
│               │                                   │                   │
│ [question]    │ 2024      2025        2026        │ Believed …        │
│               │ EXP-07 ─→ EXP-13 ──→ EXP-21        │ Observed …        │
│ Suggested:    │  FAIL     SUCCESS    SUCCESS      │ Now know …        │
│ • What did…   │  "Gamif. hurts" ── REVISED ──      │ Unknown …         │
│ • Was our…    │                                   │                   │
│ • What next?  │ [Timeline | Clean comparisons |   │ [Add evidence]    │
│               │  Coverage map]                    │ [Record decision] │
├───────────────┴───────────────────────────────────┴───────────────────┤
│ MEMORY TRACE  RETAIN → RECALL → COMPARE → REVISE → COVERAGE → ANSWER  │
└───────────────────────────────────────────────────────────────────────┘
```

### Colors

- **Cobalt:** memory links and clean comparisons
- **Green:** belief held up, positive result
- **Red:** negative result, revised belief
- **Amber:** challenged belief, confounded comparison
- **Grey:** inconclusive or untested
- **Violet:** Hindsight calls

### Centerpiece: the Learning Timeline

Experiments sit on a time axis. **Belief lanes** run underneath: each belief starts at the experiment that created it, and changes color when later evidence challenges or revises it. Clean comparisons are drawn as solid cobalt arcs; confounded comparisons as dashed amber arcs.

---

## 13. The 3-Minute Demo Script

**0:00–0:20: The pain.**
"NOVA's growth team shelved gamified onboarding two years ago after one bad test. The PM who ran it has since moved teams. Now someone wants to try it again. Should they?"

**0:20–0:40: Amnesia Mode.**
Ask "Should we bring gamified onboarding back?" The answer: "gamification can improve engagement when implemented thoughtfully." Generic and useless.

**0:40–1:30: Memory ON.**
Same question. The memory trace fills. The timeline shows EXP-07 failing, then EXP-13 and EXP-21 succeeding. RETRACE highlights **EXP-07 vs EXP-13 as a clean comparison: the only difference was 7 vs 3 steps.** The belief "gamification hurts onboarding" turns red: **Revised.** EXP-21 is shown as supporting but confounded. The underpowered and outage-affected tests are flagged, not trusted.

**1:30–2:00: What haven't we tested?**
Open the coverage map. The one untested cell lights up: **Gamification + 3 steps + new users + iOS.** "This would test an unresolved question. It is not a guarantee."

**2:00–2:35: It learns.**
Add EXP-24's result (pushes at 2/day: +3%). The belief "push notifications hurt retention" moves from Challenged to **Revised**, live. Record the decision "running the iOS test as EXP-25," then ask "what next?" RETRACE now knows EXP-25 is planned and suggests the next gap.

**2:35–3:00: Close.**
"RETRACE doesn't search the past. It tells you what the past taught you, and what it didn't."

---

## 14. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Python FastAPI |
| Memory | Hindsight Cloud (promo code MEMHACK99) or self-hosted Hindsight |
| LLM | Groq or OpenRouter, `openai/gpt-oss-120b` (fallback `qwen/qwen3-32b`) |
| Reuse from ORIGIN | Hindsight wrapper, write-through ledger, LLM retry/fallback layer, memory trace UI, theme |

All LLM calls validated with Pydantic, with retries and a deterministic fallback so the demo never breaks.

---

## 15. Scope

### Must Have

1. NOVA dataset with the three hidden patterns and three decoys
2. Question router (A–E) with fallback
3. Clean-comparison finder
4. Belief tracking with statuses
5. Weak-evidence flags (small sample, external event, different feature area)
6. Coverage map with next-experiment ranking
7. Learning Timeline with belief lanes
8. Add evidence / record decision → retained → answer updates
9. Amnesia Mode
10. Memory trace panel
11. Demo reset

### Nice to Have

- Full experiment browser
- Upload your own experiment (form)
- Export a "what we learned" brief as a document

### Non-Goals

- No PDF or CSV chatbot, no generic RAG
- No dashboards of charts that don't answer a question
- No automatic experiment execution
- No causal-inference claims
- No 100-experiment dataset nobody can follow

---

## 16. Judging Criteria Map

| Criteria | Weight | How RETRACE scores |
|---|---|---|
| Innovation | 30% | Tracks how *beliefs* evolve, not just results; finds untested combinations; a fresh Product & Strategy lane |
| Use of Hindsight Memory | 25% | Beliefs, evidence and decisions are dated memories; the answer changes live when new evidence is retained; Amnesia Mode comparison |
| Technical Implementation | 20% | Clean-comparison logic, weak-evidence flags, deterministic coverage ranking, validated LLM output |
| User Experience | 15% | One-screen layout, the Learning Timeline, suggested questions, a story told in 60 seconds |
| Real-world Impact | 10% | Stops teams repeating experiments or killing good ideas; a clear buyer in product and growth leaders |

---

## 17. Submission Checklist

- [ ] GitHub repo with README, `.env.example` and architecture diagram
- [ ] README section **"How RETRACE Uses Hindsight"**
- [ ] Demo video under 3 minutes (Section 13)
- [ ] Live demo tested with reset
- [ ] Every team member: article, social post and video (per the content guide)

> **RETRACE gives experiments a memory, so a team's past failures become lessons instead of rumors.**
