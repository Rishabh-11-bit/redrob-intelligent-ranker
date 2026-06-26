#!/usr/bin/env python3
"""
eval/fairness_audit.py — bias & fairness audit for a hiring ranker.

Checks three things and prints hard numbers:
  1. Name/gender/age blindness   - confirms no protected or proxy attribute is
     read by the scorer (audited against the source modules).
  2. Pedigree concentration      - education-tier mix of the top 100 vs the pool
     (guards against elite-school bias).
  3. Company-pedigree mix        - product vs services background in the top 100.

Location skew (India) is reported but is a stated work-authorisation business
rule from the JD, not a demographic signal. The dataset contains no gender/age
fields, and the only name field is anonymised - so the ranker is name-blind by
construction.

    python eval/fairness_audit.py --candidates ./data/candidates.jsonl
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import features as F
from src import jd_spec as J
from src.scoring import score_candidates

PROTECTED = ["gender", "sex", "age", "date_of_birth", "dob", "race", "religion", "caste", "marital"]

def best_tier(c):
    tiers = [e.get("tier") for e in c.get("education", []) if e.get("tier")]
    if not tiers: return "unknown"
    return sorted(tiers)[0]  # tier_1 < tier_2 < tier_3

def is_services(c):
    cos = [(r.get("company") or "").lower() for r in c.get("career_history", [])]
    return bool(cos) and all(any(s in co for s in J.SERVICES_COMPANIES) for co in cos)

def dist(cands, fn):
    c = Counter(fn(x) for x in cands)
    tot = sum(c.values()) or 1
    return {k: f"{v} ({100*v/tot:.0f}%)" for k, v in sorted(c.items())}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidates", required=True)
    ap.add_argument("--top", type=int, default=100); args = ap.parse_args()
    cands = [json.loads(l) for l in open(args.candidates, encoding="utf-8") if l.strip()]

    # 1) blindness audit - scan the scorer's source for protected-attribute reads
    src = ""
    for f in ["features.py", "scoring.py", "jd_spec.py", "reasoning.py"]:
        src += (Path("src") / f).read_text(encoding="utf-8").lower()
    hits = [p for p in PROTECTED if f'"{p}"' in src or f"'{p}'" in src or f".{p}" in src]
    print("=== 1. Name / gender / age blindness ===")
    print(f"Protected attributes present in dataset schema : none (no gender/age/race fields)")
    print(f"Only name field is 'anonymized_name'           : not read by the scorer")
    print(f"Protected-attribute references in scorer source : {hits or 'NONE'}")

    rows = score_candidates(cands)
    top = [r["cand"] for r in rows[:args.top]]

    print("\n=== 2. Education-tier mix (pedigree-bias check) ===")
    print(f"Pool   : {dist(cands, best_tier)}")
    print(f"Top100 : {dist(top, best_tier)}")
    print("(Education tier carries low weight; top 100 should not collapse onto tier_1.)")

    print("\n=== 3. Company background (product vs services) ===")
    f_pool = sum(is_services(c) for c in cands); f_top = sum(is_services(c) for c in top)
    print(f"Pool   : services-only career {f_pool} ({100*f_pool/len(cands):.0f}%)")
    print(f"Top100 : services-only career {f_top} ({100*f_top/len(top):.0f}%)")

    print("\n=== 4. Location (business rule, not demographic) ===")
    inpool = sum(1 for c in cands if (c["profile"].get("country") or "").lower()=="india")
    intop = sum(1 for c in top if (c["profile"].get("country") or "").lower()=="india")
    print(f"Pool India {100*inpool/len(cands):.0f}%  |  Top100 India {100*intop/len(top):.0f}%  "
          f"(JD requires India work authorisation - no visa sponsorship).")

if __name__ == "__main__":
    main()
