#!/usr/bin/env python3
"""
eval/evaluate.py — LOCAL validation harness.

There is no public leaderboard and only 3 submissions are allowed, so you must
validate locally before submitting. This script does two things:

  1. Builds a transparent SILVER relevance label per candidate from an
     INDEPENDENT rubric (deliberately built from raw schema fields, not from the
     ranker's own component scores) and reports NDCG@10, NDCG@50, MAP, P@10 of a
     submission against it. This is a PROXY for the hidden ground truth — useful
     for catching regressions between iterations, NOT for predicting your final
     score. Treat movement, not absolute value, as the signal.

  2. Runs GUARDRAIL checks that are non-circular and map directly to
     disqualification rules: honeypot rate in top 100, count of non-technical
     roles in the top 100, count of non-India candidates, and score monotonicity.

    python eval/evaluate.py --candidates ./data/candidates.jsonl --submission ./submission.csv
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import features as F
from src import jd_spec as J


def silver_tier(c: dict) -> int:
    """Independent 0-4 relevance tier from raw fields. Honeypots forced to 0."""
    if F.is_honeypot(c)[0]:
        return 0
    title = (c["profile"].get("current_title") or "").lower()
    txt = F.career_text(c)
    country = (c["profile"].get("country") or "").lower()
    relo = bool(c.get("redrob_signals", {}).get("willing_to_relocate"))
    rr = float(c.get("redrob_signals", {}).get("recruiter_response_rate", 0) or 0)

    core = any(t in title for t in J.CORE_AI_TITLES)
    adjacent = any(t in title for t in J.ADJACENT_TECH_TITLES)
    nontech = any(t in title for t in J.NON_TECH_TITLES)
    strong_ev = sum(1 for t in J.BUILD_EVIDENCE_STRONG if t in txt)
    in_india = country == "india"
    available = rr >= 0.2

    if nontech:                       # the trap bucket
        return 0
    if core and strong_ev >= 1 and (in_india or relo) and available:
        return 4
    if core and (in_india or relo):
        return 3
    if (core or adjacent) and strong_ev >= 1 and (in_india or relo):
        return 3
    if adjacent and (in_india or relo):
        return 2
    if core or adjacent:
        return 1
    return 0


def dcg(rels: list[int], k: int) -> float:
    return sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels[:k]))


def ndcg(rels: list[int], k: int) -> float:
    ideal = sorted(rels, reverse=True)
    idcg = dcg(ideal, k)
    return dcg(rels, k) / idcg if idcg > 0 else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--submission", required=True)
    args = ap.parse_args()

    cand = {}
    for line in open(args.candidates, encoding="utf-8"):
        if line.strip():
            c = json.loads(line)
            cand[c["candidate_id"]] = c

    rows = list(csv.DictReader(open(args.submission, encoding="utf-8")))
    ranked = [cand[r["candidate_id"]] for r in rows]
    rels = [silver_tier(c) for c in ranked]

    # NDCG normalized against the best achievable from the whole pool's top tiers
    pool_rels = sorted((silver_tier(c) for c in cand.values()), reverse=True)
    def ndcg_vs_pool(k):
        idcg = dcg(pool_rels, k)
        return dcg(rels, k) / idcg if idcg > 0 else 0.0

    # MAP over relevant (tier>=3) within the submitted list
    rel_bin = [1 if r >= 3 else 0 for r in rels]
    hits, precisions = 0, []
    for i, b in enumerate(rel_bin, start=1):
        if b:
            hits += 1
            precisions.append(hits / i)
    mapv = sum(precisions) / max(1, sum(rel_bin))
    p10 = sum(rel_bin[:10]) / 10

    composite = 0.50 * ndcg_vs_pool(10) + 0.30 * ndcg_vs_pool(50) + 0.15 * mapv + 0.05 * p10

    print("=== SILVER METRICS (local proxy — track movement, not absolute) ===")
    print(f"NDCG@10 : {ndcg_vs_pool(10):.4f}")
    print(f"NDCG@50 : {ndcg_vs_pool(50):.4f}")
    print(f"MAP     : {mapv:.4f}")
    print(f"P@10    : {p10:.4f}")
    print(f"COMPOSITE (0.5/0.3/0.15/0.05): {composite:.4f}")

    # ---- guardrails (non-circular, map to DQ rules) ----
    honey = sum(1 for c in ranked if F.is_honeypot(c)[0])
    nontech = sum(1 for c in ranked
                  if any(t in (c["profile"].get("current_title") or "").lower()
                         for t in J.NON_TECH_TITLES))
    foreign = sum(1 for c in ranked if (c["profile"].get("country") or "").lower() != "india")
    scores = [float(r["score"]) for r in rows]
    mono = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))

    print("\n=== GUARDRAILS ===")
    print(f"Honeypots in top 100      : {honey}   (DQ if >10)  -> {'OK' if honey <= 10 else 'FAIL'}")
    print(f"Non-technical in top 100  : {nontech} (should be ~0) -> {'OK' if nontech <= 2 else 'CHECK'}")
    print(f"Non-India in top 100      : {foreign} (relocation-only) -> {'OK' if foreign <= 8 else 'CHECK'}")
    print(f"Score non-increasing      : {mono} -> {'OK' if mono else 'FAIL'}")


if __name__ == "__main__":
    main()
