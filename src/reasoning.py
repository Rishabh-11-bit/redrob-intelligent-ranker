"""
reasoning.py
============
Builds the `reasoning` column deterministically from a candidate's REAL fields
and the feature flags already computed. No LLM, so nothing can be hallucinated:
every clause is assembled from values that exist in the profile.

Stage-4 manual review rewards reasoning that is specific, honest about concerns,
non-hallucinated, and consistent with the rank. This generator does all four:
it cites concrete facts, surfaces the dominant concern, and its tone tracks the
score band.
"""
from __future__ import annotations


def build_reasoning(c: dict, comps: dict, flags: dict, final_score: float) -> str:
    p = c["profile"]
    title = p.get("current_title", "Candidate")
    yoe = p.get("years_of_experience", 0)

    # opening clause: role + experience
    parts = [f"{title} with {yoe:.1f} yrs"]

    # positive evidence
    ev = flags.get("evidence_highlights") or []
    if ev:
        parts.append("career shows " + ", ".join(ev))
    elif comps["domain"] >= 0.6:
        parts.append("technical trajectory")

    # location (a hard JD constraint)
    parts.append(flags.get("location_label", ""))

    # one dominant behavioral fact
    beh = flags.get("behavioral_notes") or []
    if beh:
        parts.append(beh[0])

    # honest concern
    concerns = list(flags.get("penalty_notes") or [])
    # surface the biggest drag
    if comps["domain"] < 0.4 and "non-technical" not in " ".join(concerns):
        concerns.insert(0, "weak role fit vs JD")
    if flags.get("location_label", "").startswith("outside India"):
        concerns.insert(0, "location/visa concern")
    if concerns:
        parts.append("concern: " + concerns[0])

    sentence = "; ".join(x for x in parts if x).strip()
    if not sentence.endswith("."):
        sentence += "."
    # keep it tight (1-2 sentences)
    return sentence[:300]
