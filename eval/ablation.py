#!/usr/bin/env python3
"""eval/ablation.py — fast ablation: features computed once, then re-weighted."""
from __future__ import annotations
import argparse, json, math, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from src import features as F
from src import jd_spec as J
from src.scoring import semantic_similarity
from eval.evaluate import silver_tier

def dcg(rels, k):
    return sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels[:k]))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidates", required=True)
    ap.add_argument("--top", type=int, default=100); args = ap.parse_args()
    cands = [json.loads(l) for l in open(args.candidates, encoding="utf-8") if l.strip()]
    n = len(cands); print(f"[ablation] {n:,} candidates - computing features once...", file=sys.stderr)

    today = date(2025, 1, 1)
    for c in cands:
        la = c.get("redrob_signals", {}).get("last_active_date")
        if la:
            try:
                d = date.fromisoformat(la);  today = d if d > today else today
            except ValueError: pass

    sem = semantic_similarity([F.semantic_doc(c) for c in cands], None, None)
    comp = {k: np.zeros(n) for k in J.WEIGHTS}
    pen = np.ones(n); beh = np.ones(n); honey = np.zeros(n, bool)
    nontech = np.zeros(n, bool); tier = np.zeros(n, int)
    for i, c in enumerate(cands):
        comp["domain"][i] = F.domain_score(c)[0]
        comp["evidence"][i] = F.evidence_score(c)[0]
        comp["semantic"][i] = sem[i]
        comp["location"][i] = F.location_score(c)[0]
        comp["credibility"][i] = F.credibility_score(c)[0]
        comp["experience"][i] = F.experience_score(c)[0]
        pen[i] = F.penalty_multiplier(c)[0]
        beh[i] = F.behavioral_multiplier(c, today)[0]
        honey[i] = F.is_honeypot(c)[0]
        nontech[i] = any(t in (c["profile"].get("current_title") or "").lower() for t in J.NON_TECH_TITLES)
        tier[i] = silver_tier(c)
    cid = np.array([c["candidate_id"] for c in cands])
    print("[ablation] features ready", file=sys.stderr)

    pool_rels = sorted(tier.tolist(), reverse=True)
    idcg10, idcg50 = dcg(pool_rels, 10), dcg(pool_rels, 50)

    def run(active, up, ub, uh):
        w = {k: J.WEIGHTS[k] for k in active}; s = sum(w.values()) or 1.0
        base = sum((w[k] / s) * comp[k] for k in active)
        final = base * (pen if up else 1.0) * (beh if ub else 1.0)
        if uh: final = np.where(honey, 0.0, final)
        order = sorted(range(n), key=lambda i: (-final[i], cid[i]))[:args.top]
        rels = [int(tier[i]) for i in order]
        return (dcg(rels, 10)/idcg10, dcg(rels, 50)/idcg50,
                int(honey[order].sum()), int(nontech[order].sum()), set(order))

    allk = list(J.WEIGHTS.keys())
    configs = [
        ("FULL system", allk, True, True, True),
        ("- honeypot kill-switch", allk, True, True, False),
        ("- behavioral multiplier", allk, True, False, True),
        ("- disqualifier penalty", allk, False, True, True),
        ("- role/title gate", [k for k in allk if k!="domain"], True, True, True),
        ("- credibility", [k for k in allk if k!="credibility"], True, True, True),
        ("- semantic (hybrid)", [k for k in allk if k!="semantic"], True, True, True),
        ("- build evidence", [k for k in allk if k!="evidence"], True, True, True),
        ("- location fit", [k for k in allk if k!="location"], True, True, True),
    ]
    full_set=None
    print(f"\n{'configuration':<26}{'NDCG@10':>9}{'NDCG@50':>9}{'honeypots':>11}{'non-tech':>9}{'top100 chg':>12}")
    print("-"*78)
    for name, ac, up, ub, uh in configs:
        n10,n50,hp,nt,oset = run(ac,up,ub,uh)
        if full_set is None:
            full_set=oset; chg="-"
        else:
            chg=str(args.top - len(full_set & oset))
        print(f"{name:<26}{n10:>9.3f}{n50:>9.3f}{hp:>11}{nt:>9}{chg:>12}")
    print("\nHoneypots / non-tech / top100-change columns are objective (not rubric-derived).")
    print("top100 chg = candidates that drop out of the top 100 when that part is removed.")

if __name__ == "__main__":
    main()
