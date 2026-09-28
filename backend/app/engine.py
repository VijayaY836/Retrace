"""RETRACE learning engine (deterministic, no LLM).

Given the records recalled from Hindsight, it computes:
  * which experiments are relevant, and which to set aside (weak / contaminated / different area)
  * clean comparisons: pairs of experiments that differ in exactly ONE condition
  * belief status: held_up / challenged / revised / weak_basis / untested_since, and its history over time
  * then vs now: which conditions of an old experiment no longer hold today
  * coverage: which condition combinations were tested, inconclusive, planned or never tried
  * next-test ranking: the untested combination that completes the most clean comparisons

The LLM only phrases the result. Every number and ID comes from here.
"""
from datetime import date, datetime
from itertools import combinations

MIN_SAMPLE = 2000        # below this an experiment is underpowered
ALPHA = 0.05             # p-value threshold for a real effect
MEANINGFUL = 0.02        # a lift change smaller than this is "no difference"

KEY_LABEL = {
    "gamification": "gamification", "onboarding_steps": "onboarding length", "segment": "segment",
    "platform": "platform", "plan_price": "plan price", "notif_per_day": "pushes per day",
    "dark_mode": "dark mode", "lesson_minutes": "lesson length",
}


def fmt_val(key, v):
    if v is None:
        return "not set"
    if key == "gamification":
        return "gamified" if v else "not gamified"
    if key == "dark_mode":
        return "dark mode on" if v else "dark mode off"
    if key == "onboarding_steps":
        return f"{v} steps"
    if key == "segment":
        return str(v).replace("_", " ")
    if key == "platform":
        return {"android": "Android", "ios": "iOS"}.get(v, v)
    if key == "plan_price":
        return f"₹{v}"
    if key == "notif_per_day":
        return f"{v} push{'es' if v != 1 else ''}/day"
    return str(v)


def pct(x):
    return f"{x * 100:+.1f}%" if abs(x) < 0.01 else f"{x * 100:+.0f}%"


def d(ts: str) -> date:
    return datetime.fromisoformat(ts).date() if "T" in ts else date.fromisoformat(ts)


def fmt_month(ts: str) -> str:
    return d(ts).strftime("%b %Y")


# ---------------------------------------------------------------- evidence quality
def quality(e: dict, events: list[dict]) -> dict:
    """Flags an experiment as ok / inconclusive (underpowered) / caution (overlaps an external event)."""
    if e["sample_size"] < MIN_SAMPLE:
        return {"level": "inconclusive", "reason": f"only {e['sample_size']:,} users (p = {e['p_value']}); too small to support any conclusion"}
    s, t = d(e["date_start"]), d(e["date_end"])
    hits = [ev for ev in events if d(ev["date_start"]) <= t and d(ev["date_end"]) >= s and ev.get("event_type") in ("sale", "outage")]
    if hits:
        return {"level": "caution", "reason": "ran during " + " and ".join(ev["note"].split(":")[0].rstrip(".") for ev in hits) + "; treat the result with caution",
                "events": [ev["event_id"] for ev in hits]}
    return {"level": "ok", "reason": ""}


def direction(e: dict) -> str:
    if e["p_value"] >= ALPHA:
        return "none"
    return "positive" if e["lift"] > 0 else "negative"


# ---------------------------------------------------------------- comparisons
def differences(a: dict, b: dict) -> list[str]:
    ca, cb = a["conditions"], b["conditions"]
    return sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))


def compare_all(exps: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (clean, confounded) comparisons among experiments with the same metric."""
    clean, confounded = [], []
    for a, b in combinations(sorted(exps, key=lambda e: e["date_end"]), 2):
        if a["primary_metric"] != b["primary_metric"]:
            continue
        diff = differences(a, b)
        if not diff:
            continue
        item = {
            "a": a["experiment_id"], "b": b["experiment_id"], "differs": diff,
            "changes": [{"key": k, "label": KEY_LABEL.get(k, k), "from": fmt_val(k, a["conditions"].get(k)), "to": fmt_val(k, b["conditions"].get(k))} for k in diff],
            "lift_a": a["lift"], "lift_b": b["lift"], "delta": round(b["lift"] - a["lift"], 3),
            "shared": {k: v for k, v in a["conditions"].items() if k not in diff},
        }
        (clean if len(diff) == 1 else confounded).append(item)
    return clean, confounded


# ---------------------------------------------------------------- beliefs
def matches(claim: dict, cond: dict) -> bool:
    v = cond.get(claim["factor"])
    if claim["op"] == "gt":
        return v is not None and v > claim["value"]
    return v == claim["value"]


def agrees(claim: dict, e: dict) -> bool:
    return direction(e) == claim["direction"]


def judge_belief(belief: dict, exps: list[dict], events: list[dict], cutoff: date | None = None) -> dict:
    """Status of a belief given the evidence available up to `cutoff` (default: all)."""
    claim, f = belief["claim"], belief["claim"]["factor"]
    by_id = {e["experiment_id"]: e for e in exps}
    src = by_id.get(belief["source_experiment"])
    bdate = d(belief["timestamp"])
    pool = [e for e in exps if e["feature_area"] == belief["feature_area"] and (cutoff is None or d(e["date_end"]) <= cutoff)]
    good = [e for e in pool if quality(e, events)["level"] == "ok"]

    if src and quality(src, events)["level"] == "inconclusive":
        return {"status": "weak_basis", "why": f"It rests on {src['experiment_id']}, which had {quality(src, events)['reason']}.",
                "later": [], "supporting_pairs": [], "contradicting_pairs": []}

    later = [e for e in good if d(e["date_end"]) > bdate and e["experiment_id"] != belief["source_experiment"] and matches(claim, e["conditions"])]
    later_items = [{"id": e["experiment_id"], "date": e["date_end"], "lift": e["lift"], "direction": direction(e),
                    "agrees": agrees(claim, e), "conditions": e["conditions"]} for e in later]

    clean, _ = compare_all(good)
    sup, con = [], []
    for c in clean:
        if c["differs"] != [f]:
            continue
        a, b = by_id[c["a"]], by_id[c["b"]]
        if max(d(a["date_end"]), d(b["date_end"])) <= bdate and belief["source_experiment"] not in (c["a"], c["b"]):
            pass  # older pairs still count as context
        ma, mb = matches(claim, a["conditions"]), matches(claim, b["conditions"])
        if ma != mb:
            m, n = (a, b) if ma else (b, a)
            effect = m["lift"] - n["lift"]
            ok = (effect < -MEANINGFUL) if claim["direction"] == "negative" else (effect > MEANINGFUL) if claim["direction"] == "positive" else abs(effect) < MEANINGFUL
            entry = {**c, "with": m["experiment_id"], "without": n["experiment_id"], "effect": round(effect, 3), "kind": "on_off"}
            (sup if ok else con).append(entry)
        elif ma and mb and direction(a) != direction(b) and "none" not in (direction(a), direction(b)):
            con.append({**c, "kind": "too_broad"})

    if con:
        status = "revised"
    elif any(not i["agrees"] for i in later_items):
        status = "challenged"
    elif later_items:
        status = "held_up"
    else:
        status = "untested_since"
    return {"status": status, "later": later_items, "supporting_pairs": sup, "contradicting_pairs": con,
            "why": _why(status, belief, later_items, sup, con, by_id)}


def _pair_txt(p, by_id):
    ch = p["changes"][0]
    return f"{p['a']} vs {p['b']} ({ch['from']} → {ch['to']}: {pct(p['lift_a'])} → {pct(p['lift_b'])})"


def _why(status, belief, later, sup, con, by_id):
    if status == "revised":
        on_off_con = [p for p in con if p["kind"] == "on_off"]
        broad = [p for p in con if p["kind"] == "too_broad"]
        if on_off_con and sup:
            ctx_s, ctx_c = sup[0]["shared"], on_off_con[0]["shared"]
            split = [k for k in ctx_s if ctx_s.get(k) != ctx_c.get(k)]
            k = split[0] if split else None
            if k:
                return (f"True only with {fmt_val(k, ctx_s[k])}: {_pair_txt(sup[0], by_id)}. "
                        f"With {fmt_val(k, ctx_c[k])} the opposite happened: {_pair_txt(on_off_con[0], by_id)}.")
        if broad:
            p = broad[0]
            return f"Too broad: it depends on {p['changes'][0]['label']}. {_pair_txt(p, by_id)}."
        return "A clean comparison contradicts it: " + "; ".join(_pair_txt(p, by_id) for p in on_off_con[:2]) + "."
    if status == "challenged":
        dis = [i for i in later if not i["agrees"]]
        i = dis[0]
        src = by_id.get(belief["source_experiment"])
        diff = [k for k in (differences(src, by_id[i["id"]]) if src else []) if k != belief["claim"]["factor"]]
        extra = f", but it also changed {', '.join(KEY_LABEL.get(k, k) for k in diff)}, so it cannot isolate the cause" if diff else ""
        return f"{i['id']} found {pct(i['lift'])}{extra}."
    if status == "held_up":
        i = later[-1]
        e = by_id[i["id"]]
        return f"{i['id']} ({fmt_month(i['date'])}) agrees: {pct(i['lift'])}, p = {e['p_value']}."
    if status == "untested_since":
        return "No later experiment has tested it."
    return ""


def belief_history(belief, exps, events, today: date) -> list[dict]:
    """Status of the belief after each new piece of evidence in its area."""
    bdate = d(belief["timestamp"])
    points = sorted({d(e["date_end"]) for e in exps if e["feature_area"] == belief["feature_area"] and d(e["date_end"]) > bdate and d(e["date_end"]) <= today})
    hist = [{"date": bdate.isoformat(), "status": judge_belief(belief, exps, events, cutoff=bdate)["status"], "by": belief["source_experiment"]}]
    for p in points:
        st = judge_belief(belief, exps, events, cutoff=p)["status"]
        if st != hist[-1]["status"]:
            by = next(e["experiment_id"] for e in exps if d(e["date_end"]) == p and e["feature_area"] == belief["feature_area"])
            hist.append({"date": p.isoformat(), "status": st, "by": by})
    return hist


# ---------------------------------------------------------------- then vs now
def state_at(product_state: list[dict], key: str, when: date):
    rows = sorted([s for s in product_state if s["key"] == key and d(s["timestamp"]) <= when], key=lambda s: s["timestamp"])
    return rows[-1] if rows else None


def then_vs_now(e: dict, product_state: list[dict], today: date, drivers: set[str]) -> dict:
    then = d(e["date_end"])
    rows = []
    c = e["conditions"]
    if "onboarding_steps" in c:
        now = state_at(product_state, "onboarding_steps", today)
        if now:
            rows.append({"key": "onboarding_steps", "label": "Onboarding length", "then": fmt_val("onboarding_steps", c["onboarding_steps"]),
                         "now": f"{now['value']} steps", "changed": now["value"] != c["onboarding_steps"], "since": now["timestamp"][:10], "matters": "onboarding_steps" in drivers})
    p_then, p_now = state_at(product_state, "platforms", then), state_at(product_state, "platforms", today)
    if p_then and p_now:
        share = state_at(product_state, "ios_share_new_users", today)
        now_txt = " + ".join(fmt_val("platform", x) for x in p_now["value"]) + (f" (iOS {share['value'] * 100:.0f}% of new users)" if share else "")
        rows.append({"key": "platform", "label": "Platforms", "then": " + ".join(fmt_val("platform", x) for x in p_then["value"]) + " only" if len(p_then["value"]) == 1 else "",
                     "now": now_txt, "changed": p_then["value"] != p_now["value"], "since": p_now["timestamp"][:10], "matters": "platform" in drivers})
    if "plan_price" in c:
        now = state_at(product_state, "plan_price", today)
        if now:
            rows.append({"key": "plan_price", "label": "Standard plan", "then": fmt_val("plan_price", c["plan_price"]), "now": fmt_val("plan_price", now["value"]),
                         "changed": now["value"] != c["plan_price"], "since": now["timestamp"][:10], "matters": "plan_price" in drivers})
    key_changed = [r for r in rows if r["changed"] and r["matters"]]
    if key_changed:
        verdict = (f"Probably not. {key_changed[0]['label']} has changed since {e['experiment_id']} "
                   f"({key_changed[0]['then']} then, {key_changed[0]['now']} now), and clean comparisons show that condition matters.")
    elif any(r["changed"] for r in rows):
        verdict = "Partly. Some conditions changed, but none that the evidence shows to matter."
    else:
        verdict = f"Likely yes. Today's conditions match those of {e['experiment_id']}."
    return {"experiment": e["experiment_id"], "rows": rows, "verdict": verdict}


# ---------------------------------------------------------------- coverage
def _cell_key(cell: dict, dims: list[str]):
    return tuple(cell[k] for k in dims)


def coverage(area: str, dims: list[str], levels: dict, exps: list[dict], events: list[dict], decisions: list[dict], focus: tuple | None = None) -> dict:
    area_exps = [e for e in exps if e["feature_area"] == area]
    grid = {}

    def cells(i, cur):
        if i == len(dims):
            yield dict(cur)
            return
        for v in levels[dims[i]]:
            cur[dims[i]] = v
            yield from cells(i + 1, cur)

    def fill(c):
        return {k: (c.get(k) if k in c else (False if k in ("gamification", "dark_mode") else None)) for k in dims}

    for c in cells(0, {}):
        grid[_cell_key(c, dims)] = {"cell": c, "status": "untested", "experiments": []}
    for e in area_exps:
        k = _cell_key(fill(e["conditions"]), dims)
        if k in grid:
            q = quality(e, events)["level"]
            g = grid[k]
            g["experiments"].append({"id": e["experiment_id"], "lift": e["lift"], "quality": q})
            if q == "ok":
                g["status"] = "tested"
            elif g["status"] == "untested":
                g["status"] = "inconclusive"
    for dec in decisions:
        if dec.get("feature_area") == area and dec.get("cell"):
            k = _cell_key({**{x: None for x in dims}, **dec["cell"]}, dims)
            if k in grid and grid[k]["status"] == "untested":
                grid[k]["status"] = "planned"
                grid[k]["planned"] = dec.get("planned_experiment")

    tested = [g for g in grid.values() if g["status"] == "tested"]
    ranked = []
    for g in grid.values():
        if g["status"] != "untested":
            continue
        nbrs = []
        for t in tested:
            diff = [k for k in dims if t["cell"][k] != g["cell"][k]]
            if len(diff) == 1:
                nbrs.append({"id": t["experiments"][0]["id"], "differs": diff[0], "label": KEY_LABEL.get(diff[0], diff[0])})
        focus_bonus = 1 if focus and g["cell"].get(focus[0]) == focus[1] else 0
        ranked.append({"cell": g["cell"], "neighbours": nbrs, "score": len(nbrs) * 2 + focus_bonus})
    ranked.sort(key=lambda r: -r["score"])
    for r in ranked:
        r["label"] = " + ".join(fmt_val(k, r["cell"][k]) for k in dims)
        if r["neighbours"]:
            parts = [f"{n['id']} (only {n['label']} differs)" for n in r["neighbours"]]
            r["why"] = (f"One step away from {', '.join(parts)}. Running it would complete {len(parts)} clean comparison"
                        f"{'s' if len(parts) > 1 else ''} and test an open question. It is not a prediction that it will work.")
        else:
            r["why"] = "No nearby tested combination; results would be hard to compare."
    rows = [{"cell": g["cell"], "status": g["status"], "experiments": g["experiments"], "planned": g.get("planned"),
             "label": " + ".join(fmt_val(k, g["cell"][k]) for k in dims)} for g in grid.values()]
    return {"dims": dims, "dim_labels": [KEY_LABEL.get(k, k) for k in dims], "levels": {k: [fmt_val(k, v) for v in levels[k]] for k in dims},
            "raw_levels": {k: levels[k] for k in dims}, "cells": rows, "ranked": ranked[:5],
            "counts": {s: sum(1 for g in grid.values() if g["status"] == s) for s in ("tested", "inconclusive", "planned", "untested")}}


# ---------------------------------------------------------------- full analysis for a topic
STATUS_NAME = {"held_up": "Held up", "challenged": "Challenged", "revised": "Revised", "weak_basis": "Weak basis", "untested_since": "Untested since"}
STATUS_PHRASE = {"held_up": "has held up", "challenged": "has been challenged", "revised": "needs revising", "weak_basis": "rests on weak evidence", "untested_since": "has not been tested since"}


def analyze(topic: dict, company: dict, records: list[dict]) -> dict:
    today = date.fromisoformat(company["today"])
    area = topic["area"]
    exps = [r for r in records if r["kind"] == "experiment"]
    beliefs = [r for r in records if r["kind"] == "belief"]
    events = [r for r in records if r["kind"] == "event"]
    states = [r for r in records if r["kind"] == "product_state"]
    decisions = [r for r in records if r["kind"] == "decision"]
    notes = [r for r in records if r["kind"] in ("observation", "note")]
    by_id = {e["experiment_id"]: e for e in exps}

    area_exps = sorted([e for e in exps if e["feature_area"] == area], key=lambda e: e["date_end"])
    q = {e["experiment_id"]: quality(e, events) for e in exps}
    good = [e for e in area_exps if q[e["experiment_id"]]["level"] == "ok"]

    kws = topic.get("keywords", [])
    set_aside = []
    for e in area_exps:
        if q[e["experiment_id"]]["level"] != "ok":
            set_aside.append({"id": e["experiment_id"], "name": e["name"], "reason": q[e["experiment_id"]]["reason"].capitalize() + ".", "kind": q[e["experiment_id"]]["level"]})
    for e in exps:
        if e["feature_area"] != area and any(k in (e["name"] + " " + e["hypothesis"]).lower() for k in kws):
            set_aside.append({"id": e["experiment_id"], "name": e["name"], "reason": f"Different feature area ({e['feature_area']}); same word, different thing.", "kind": "different_area"})

    clean, confounded = compare_all(good)
    drivers = {c["differs"][0] for c in clean if abs(c["delta"]) >= 0.05}
    strongest = max(clean, key=lambda c: abs(c["delta"])) if clean else None

    topic_beliefs = [b for b in beliefs if b["feature_area"] == area and (topic.get("factor") is None or b["claim"]["factor"] == topic["factor"])]
    other_beliefs = [b for b in beliefs if b["feature_area"] == area and b not in topic_beliefs]
    judged = []
    for b in sorted(topic_beliefs, key=lambda b: b["timestamp"]) + sorted(other_beliefs, key=lambda b: b["timestamp"]):
        j = judge_belief(b, exps, events)
        judged.append({"id": b["belief_id"], "statement": b["statement"], "date": b["timestamp"][:10], "source": b["source_experiment"], "author": b.get("author"),
                       "status": j["status"], "status_name": STATUS_NAME[j["status"]], "why": j["why"], "later": j["later"],
                       "supporting_pairs": j["supporting_pairs"], "contradicting_pairs": j["contradicting_pairs"],
                       "history": belief_history(b, exps, events, today), "primary": b in topic_beliefs})

    main = judged[0] if judged else None
    tvn = then_vs_now(by_id[main["source"]], states, today, drivers) if main and main["source"] in by_id else None

    area_cfg = company["areas"][area]
    focus = (topic["factor"], main and next((b["claim"]["value"] for b in beliefs if b["belief_id"] == main["id"]), None)) if topic.get("factor") and main else None
    if focus and focus[0] == "notif_per_day":
        focus = None
    cov = coverage(area, area_cfg["coverage_dims"], {k: company["dim_levels"][k] for k in area_cfg["coverage_dims"]}, exps, events, decisions, focus)
    planned = [dec for dec in decisions if dec.get("feature_area") == area]

    area_notes = [n for n in notes if n.get("feature_area") in (area, None)]
    timeline = {
        "experiments": [{"id": e["experiment_id"], "name": e["name"], "date": e["date_end"], "lift": e["lift"], "direction": direction(e),
                         "quality": q[e["experiment_id"]]["level"], "conditions": e["conditions"], "interpretation": e["team_interpretation"]} for e in area_exps],
        "beliefs": [{"id": j["id"], "statement": j["statement"], "date": j["date"], "history": j["history"], "status": j["status"]} for j in judged],
        "notes": [{"id": n.get("observation_id") or n.get("note_id"), "date": n["timestamp"][:10], "text": n["note"], "author": n.get("author"), "from_chat": n.get("source") == "chat"} for n in area_notes],
        "product_changes": [{"id": s["state_id"], "date": s["timestamp"][:10], "text": s["note"]} for s in states if d(s["timestamp"]) >= d(area_exps[0]["date_start"]) if area_exps],
        "range": [area_exps[0]["date_start"] if area_exps else "2024-01-01", company["today"]],
    }

    return {
        "topic": topic, "area": area, "area_label": area_cfg["label"], "metric": area_cfg["metric"],
        "experiments": [{**e, "quality": q[e["experiment_id"]]} for e in area_exps],
        "beliefs": judged, "main_belief": main,
        "clean": clean, "confounded": confounded[:12], "strongest": strongest, "drivers": sorted(drivers),
        "set_aside": set_aside, "then_vs_now": tvn, "coverage": cov, "planned": planned, "notes": area_notes, "timeline": timeline,
        "counts": {"experiments": len(area_exps), "usable": len(good), "clean": len(clean), "confounded": len(confounded), "set_aside": len(set_aside)},
    }


def now_know(a: dict) -> str:
    """Plain summary built only from computed facts (used as the LLM's ground truth and as fallback)."""
    m = a["main_belief"]
    if not m:
        return "There is no recorded team belief on this topic yet."
    s = a["strongest"]
    driver = ""
    if s and m["status"] == "revised":
        ch = s["changes"][0]
        driver = f" The biggest single difference came from {ch['label']}: {s['a']} vs {s['b']} ({ch['from']} → {ch['to']}) moved the result from {pct(s['lift_a'])} to {pct(s['lift_b'])}."
    return f"“{m['statement']}” {STATUS_PHRASE[m['status']]}. {m['why']}{driver}"
