"""
eval/harness.py — shared evaluation engine for ablation and weight-tuning.

Computes every scoring component ONCE for all candidates and caches them, so
ablation (toggling components) and tuning (re-weighting) are instant re-combinations
rather than full re-runs.

Silver labels come from an INDEPENDENT heuristic rubric that leans on signals the
production ranker does NOT use — skill-assessment scores, total endorsements,
GitHub activity, education tier — so ablation deltas measure real contribution
rather than a tautology. For gold labels, see eval/llm_judge.py.

    python eval/harness.py build      # build the cache (run once)
"""
from __future__ import annotations
import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import features as F
from src import jd_spec as J
from src.scoring import semantic_similarity

CACHE = Path(__file__).resolve().parent / "cache.npz"
DATA = Path(__file__).resolve().parents[1] / "data" / "candidates.jsonl"

COMPONENTS = ["domain", "evidence", "semantic", "location", "credibility", "experience"]


def _today(cands):
    t = date(2025, 1, 1)
    for c in cands:
        la = c.get("redrob_signals", {}).get("last_active_date")
        if la:
            try:
                d = date.fromisoformat(la)
                t = max(t, d)
            except ValueError:
                pass
    return t


def silver_tier(c: dict) -> int:
    """Independent 0-4 relevance tier. Honeypots and non-technical titles -> 0."""
    if F.is_honeypot(c)[0]:
        return 0
    title = (c["profile"].get("current_title") or "").lower()
    if any(t in title for t in J.NON_TECH_TITLES):
        return 0
    txt = F.career_text(c)
    s = c.get("redrob_signals", {})
    country = (c["profile"].get("country") or "").lower()
    relo = bool(s.get("willing_to_relocate"))

    p = 0.0
    if any(t in title for t in J.CORE_AI_TITLES):
        p += 3
    elif any(t in title for t in J.ADJACENT_TECH_TITLES):
        p += 1.5
    p += min(3, sum(1 for t in J.BUILD_EVIDENCE_STRONG if t in txt))
    in_scope = (country == "india") or relo
    if not in_scope:
        p = min(p, 1.5)  # abroad, no relocation: hard cap
    elif country == "india":
        p += 2
    yoe = float(c["profile"].get("years_of_experience", 0) or 0)
    if 5 <= yoe <= 9:
        p += 1
    # --- independent competence signals (ranker does not weight these directly) ---
    asmt = s.get("skill_assessment_scores", {}) or {}
    am = (sum(asmt.values()) / len(asmt) / 100.0) if asmt else 0.0
    if am >= 0.6:
        p += 1.5
    elif am >= 0.4:
        p += 0.5
    if (s.get("endorsements_received", 0) or 0) >= 25:
        p += 0.5
    if (s.get("github_activity_score", 0) or 0) >= 6:
        p += 0.5
    # (education tier deliberately excluded - see fairness audit)
    # availability
    if float(s.get("recruiter_response_rate", 0) or 0) >= 0.3:
        p += 1
    if s.get("open_to_work_flag"):
        p += 0.5

    if p >= 8: return 4
    if p >= 6: return 3
    if p >= 4: return 2
    if p >= 2: return 1
    return 0


def build():
    cands = [json.loads(l) for l in open(DATA, encoding="utf-8") if l.strip()]
    print(f"[harness] {len(cands):,} candidates")
    today = _today(cands)
    docs = [F.semantic_doc(c) for c in cands]
    sem = semantic_similarity(docs, None, None)

    n = len(cands)
    arr = {k: np.zeros(n, dtype="float32") for k in COMPONENTS}
    penalty = np.ones(n, dtype="float32")
    behavioral = np.ones(n, dtype="float32")
    honeypot = np.zeros(n, dtype=bool)
    nontech = np.zeros(n, dtype=bool)
    foreign = np.zeros(n, dtype=bool)
    silver = np.zeros(n, dtype="int8")

    for i, c in enumerate(cands):
        arr["domain"][i] = F.domain_score(c)[0]
        arr["evidence"][i] = F.evidence_score(c)[0]
        arr["semantic"][i] = sem[i]
        arr["location"][i] = F.location_score(c)[0]
        arr["credibility"][i] = F.credibility_score(c)[0]
        arr["experience"][i] = F.experience_score(c)[0]
        penalty[i] = F.penalty_multiplier(c)[0]
        behavioral[i] = F.behavioral_multiplier(c, today)[0]
        honeypot[i] = F.is_honeypot(c)[0]
        title = (c["profile"].get("current_title") or "").lower()
        nontech[i] = any(t in title for t in J.NON_TECH_TITLES)
        foreign[i] = (c["profile"].get("country") or "").lower() != "india"
        silver[i] = silver_tier(c)

    ids = np.array([c["candidate_id"] for c in cands])
    np.savez_compressed(CACHE, ids=ids, penalty=penalty, behavioral=behavioral,
                        honeypot=honeypot, nontech=nontech, foreign=foreign,
                        silver=silver, **arr)
    print(f"[harness] cached -> {CACHE}")
    from collections import Counter
    print("[harness] silver tier distribution:", dict(sorted(Counter(silver.tolist()).items())))


def load():
    d = np.load(CACHE, allow_pickle=True)
    return d


def combine(d, weights=None, flags=None):
    """Recombine cached components into final scores. flags can disable parts."""
    weights = weights or dict(J.WEIGHTS)
    flags = flags or {}
    n = len(d["ids"])
    base = np.zeros(n, dtype="float64")
    wsum = sum(weights.values())
    for k, w in weights.items():
        if flags.get(f"drop_{k}"):
            continue
        base += (w / wsum) * d[k]
    scores = base
    if not flags.get("drop_penalty"):
        scores = scores * d["penalty"]
    if not flags.get("drop_behavioral"):
        scores = scores * d["behavioral"]
    if not flags.get("drop_honeypot"):
        scores = np.where(d["honeypot"], 0.0, scores)
    return scores


def ndcg(rels, k):
    def dcg(r):
        return sum((2 ** x - 1) / math.log2(i + 2) for i, x in enumerate(r[:k]))
    ideal = sorted(rels, reverse=True)
    idcg = dcg(ideal)
    return dcg(rels) / idcg if idcg > 0 else 0.0


def evaluate(d, scores, k=100):
    order = np.lexsort((d["ids"], -scores))[:k]   # score desc, id asc
    silver = d["silver"]
    pool = sorted(silver.tolist(), reverse=True)
    ranked = [int(silver[i]) for i in order]

    def dcg(r, kk):
        return sum((2 ** x - 1) / math.log2(i + 2) for i, x in enumerate(r[:kk]))
    def ndcg_pool(kk):
        idcg = dcg(pool, kk)
        return dcg(ranked, kk) / idcg if idcg > 0 else 0.0

    rel = [1 if r >= 3 else 0 for r in ranked]
    hits, precs = 0, []
    for i, b in enumerate(rel, 1):
        if b:
            hits += 1; precs.append(hits / i)
    mapv = sum(precs) / max(1, sum(rel))
    p10 = sum(rel[:10]) / 10
    comp = 0.50 * ndcg_pool(10) + 0.30 * ndcg_pool(50) + 0.15 * mapv + 0.05 * p10
    return {
        "NDCG@10": ndcg_pool(10), "NDCG@50": ndcg_pool(50),
        "MAP": mapv, "P@10": p10, "COMPOSITE": comp,
        "honeypots": int(d["honeypot"][order].sum()),
        "nontech": int(d["nontech"][order].sum()),
        "foreign": int(d["foreign"][order].sum()),
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build()
    else:
        d = load()
        print(evaluate(d, combine(d)))


def evaluate_masked(d, scores, mask, k=100):
    """Evaluate only within a subset (mask) of candidates - a harder pool where
    coarse gates don't apply, exposing the nuanced components' contribution."""
    import numpy as np, math
    idx = np.where(mask)[0]
    sub_scores = scores[idx]; sub_silver = d["silver"][idx]; sub_ids = d["ids"][idx]
    order = np.lexsort((sub_ids, -sub_scores))[:k]
    ranked = [int(sub_silver[i]) for i in order]
    pool = sorted(sub_silver.tolist(), reverse=True)
    def dcg(r, kk):
        return sum((2**x - 1)/math.log2(i+2) for i, x in enumerate(r[:kk]))
    def nd(kk):
        idcg = dcg(pool, kk); return dcg(ranked, kk)/idcg if idcg > 0 else 0.0
    rel = [1 if r >= 3 else 0 for r in ranked]
    hits, precs = 0, []
    for i, b in enumerate(rel, 1):
        if b: hits += 1; precs.append(hits/i)
    mapv = sum(precs)/max(1, sum(rel))
    return {"NDCG@10": nd(10), "NDCG@50": nd(50),
            "COMPOSITE": 0.5*nd(10)+0.3*nd(50)+0.15*mapv+0.05*(sum(rel[:10])/10)}
