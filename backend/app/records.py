"""Turns RETRACE records into Hindsight memories.

Each record is ONE memory with: a plain-English narrative (what Hindsight extracts
facts from), its real date (for temporal recall), tags (kind / area / experiment),
a document_id, and the full structured record in metadata.
"""
import json
from datetime import datetime

from .config import SOURCE_TAG

ID_FIELDS = ["experiment_id", "belief_id", "observation_id", "state_id", "event_id", "decision_id", "note_id", "qa_id"]


def record_id(r: dict) -> str:
    return next(r[f] for f in ID_FIELDS if r.get(f))


def fmt_cond(c: dict) -> str:
    from .engine import KEY_LABEL, fmt_val
    return ", ".join(f"{KEY_LABEL.get(k, k)}: {fmt_val(k, v)}" for k, v in c.items())


def narrative(r: dict) -> str:
    k = r["kind"]
    when = datetime.fromisoformat(r["timestamp"]).strftime("%d %b %Y")
    if k == "experiment":
        return (f"Experiment {r['experiment_id']} '{r['name']}' ({r['feature_area']}) ran {r['date_start']} to {r['date_end']}, owned by {r['owner']}. "
                f"Hypothesis: {r['hypothesis']}. Conditions: {fmt_cond(r['conditions'])}. "
                f"Result on {r['primary_metric']}: control {r['control_rate']}, variant {r['variant_rate']}, lift {r['lift'] * 100:+.1f}% "
                f"(n = {r['sample_size']:,}, p = {r['p_value']}). Team interpretation at the time: \"{r['team_interpretation']}\" Decision: {r['decision']}.")
    if k == "belief":
        return f"Team belief recorded on {when} by {r.get('author', 'the team')} after {r['source_experiment']}: \"{r['statement']}\" (area: {r['feature_area']})."
    if k in ("observation", "note"):
        return f"{'Observation' if k == 'observation' else 'Team note'} on {when} by {r.get('author', 'the team')} ({r.get('feature_area') or 'general'}): {r['note']}"
    if k == "product_state":
        return f"Product change on {when}: {r['note']}"
    if k == "event":
        return f"External event from {r['date_start']} to {r['date_end']} ({r['event_type']}): {r['note']}"
    if k == "decision":
        return f"Decision on {when} ({r['feature_area']}): {r['note']}"
    if k == "qa":
        return f"RETRACE answered on {when}: Q: \"{r['question']}\" A: {r['answer']}"
    return json.dumps(r)


def tags_for(r: dict) -> list[str]:
    tags = [SOURCE_TAG, f"kind:{r['kind']}"]
    if r.get("feature_area"):
        tags.append(f"area:{r['feature_area']}")
    if r.get("experiment_id"):
        tags.append(f"exp:{r['experiment_id']}")
    if r.get("source_experiment"):
        tags.append(f"exp:{r['source_experiment']}")
    return tags


def to_memory_item(r: dict) -> dict:
    return {
        "content": narrative(r),
        "timestamp": datetime.fromisoformat(r["timestamp"]),
        "context": f"NOVA product experimentation history: {r['kind']}",
        "document_id": record_id(r),
        "metadata": {"record_id": record_id(r), "kind": r["kind"], "record_json": json.dumps(r, ensure_ascii=False)},
        "tags": tags_for(r),
    }
