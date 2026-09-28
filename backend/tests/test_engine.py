"""The engine must discover NOVA's hidden stories from the data alone."""
import json
from datetime import date
from pathlib import Path

from app import engine

DATA = Path(__file__).resolve().parent.parent / "data" / "nova"


def load(extra=None):
    recs = []
    for f in ["experiments", "beliefs", "observations", "product_state", "events"]:
        recs += json.loads((DATA / f"{f}.json").read_text())
    return recs + (extra or [])


COMPANY = json.loads((DATA / "company.json").read_text())
DEMO = json.loads((DATA / "demo.json").read_text())
TOPIC = {t["id"]: t for t in COMPANY["topics"]}


def test_gamification_belief_is_revised_and_depends_on_onboarding_length():
    a = engine.analyze(TOPIC["gamification"], COMPANY, load())
    m = a["main_belief"]
    assert m["id"] == "BEL-07" and m["status"] == "revised"
    assert "3 steps" in m["why"] and "7 steps" in m["why"]


def test_clean_comparisons_found():
    a = engine.analyze(TOPIC["gamification"], COMPANY, load())
    pairs = {(c["a"], c["b"]) for c in a["clean"]}
    for p in [("EXP-07", "EXP-13"), ("EXP-04", "EXP-07"), ("EXP-10", "EXP-13"), ("EXP-04", "EXP-10")]:
        assert p in pairs, p
    assert a["strongest"]["a"] == "EXP-07" and a["strongest"]["b"] == "EXP-13"


def test_confounded_evidence_is_labelled():
    a = engine.analyze(TOPIC["gamification"], COMPANY, load())
    c = next(c for c in a["confounded"] if c["a"] == "EXP-13" and c["b"] == "EXP-21")
    assert set(c["differs"]) == {"segment", "platform", "plan_price"}


def test_referral_decoy_set_aside():
    a = engine.analyze(TOPIC["gamification"], COMPANY, load())
    assert any(s["id"] == "EXP-22" and s["kind"] == "different_area" for s in a["set_aside"])


def test_top_gap_is_gamified_short_onboarding_for_new_ios_users():
    a = engine.analyze(TOPIC["gamification"], COMPANY, load())
    top = a["coverage"]["ranked"][0]["cell"]
    assert top == {"gamification": True, "onboarding_steps": 3, "segment": "new_users", "platform": "ios"}
    assert len(a["coverage"]["ranked"][0]["neighbours"]) == 3


def test_planned_decision_changes_next_suggestion():
    a = engine.analyze(TOPIC["gamification"], COMPANY, load([DEMO["decision"]]))
    assert a["coverage"]["ranked"][0]["cell"] != DEMO["decision"]["cell"]
    assert a["coverage"]["counts"]["planned"] == 1


def test_then_vs_now_old_failure_no_longer_applies():
    a = engine.analyze(TOPIC["gamification"], COMPANY, load())
    tvn = a["then_vs_now"]
    assert tvn["verdict"].startswith("Probably not")
    assert any(r["key"] == "onboarding_steps" and r["changed"] for r in tvn["rows"])


def test_dark_mode_held_up():
    a = engine.analyze(TOPIC["dark_mode"], COMPANY, load())
    assert a["main_belief"]["status"] == "held_up"


def test_annual_plan_belief_has_weak_basis():
    a = engine.analyze(TOPIC["annual_plan"], COMPANY, load())
    assert a["main_belief"]["status"] == "weak_basis"


def test_paywall_experiment_flagged_for_sale_and_outage():
    a = engine.analyze(TOPIC["paywall"], COMPANY, load())
    assert any(s["id"] == "EXP-19" and s["kind"] == "caution" for s in a["set_aside"])


def test_push_belief_challenged_then_revised_after_new_result():
    before = engine.analyze(TOPIC["notifications"], COMPANY, load())
    assert before["main_belief"]["status"] == "challenged"
    after = engine.analyze(TOPIC["notifications"], COMPANY, load([DEMO["new_result"]]))
    assert after["main_belief"]["status"] == "revised"
    assert [h["status"] for h in after["main_belief"]["history"]] == ["untested_since", "challenged", "revised"]
