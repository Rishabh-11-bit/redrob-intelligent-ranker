#!/usr/bin/env python3
"""
eval/llm_judge.py — INDEPENDENT evaluation with an LLM judge (run offline).

The built-in silver rubric (eval/evaluate.py) shares assumptions with the
ranker, so it can only catch regressions, not prove absolute quality. This
script removes that circularity: an LLM that has never seen our scoring logic
reads the JD and each candidate and assigns a relevance tier 0-4. We then score
our ranking against those labels with NDCG - a genuine, third-party check.

This is a DEV-TIME tool. It needs network + an API key and is never part of the
ranking step (which stays offline). Judge a stratified sample (cheap), not all
100K.

    pip install anthropic
    set ANTHROPIC_API_KEY=...           (Windows)   /   export on mac/linux
    python eval/llm_judge.py --candidates ./data/candidates.jsonl --sample 200

Outputs eval/llm_labels.json and prints NDCG@10 / NDCG@50 of our ranking vs the
LLM judge.
"""
from __future__ import annotations
import argparse, json, math, os, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.jd_spec import JD_QUERY
from src.scoring import score_candidates

RUBRIC = """You are a senior engineering hiring manager. Score how well a candidate fits
this role on a 0-4 scale:
4 = excellent fit (shipped production ranking/search/recommendation/retrieval systems
    at a product company, ~6-8 yrs, strong applied ML, India-based or relocating)
3 = good fit (relevant production ML/eng + India/relocate)
2 = plausible (adjacent technical background)
1 = weak (technical but off-target)
0 = not a fit (non-technical, keyword-stuffer, services-only, abroad/no-relocate, or
    an impossible/inconsistent profile)
Reply with ONLY the integer 0-4."""

def profile_blurb(c):
    p = c["profile"]; sig = c.get("redrob_signals", {})
    hist = "; ".join(f"{r.get('title')} @ {r.get('company')} ({r.get('duration_months',0)}mo): "
                     f"{(r.get('description') or '')[:160]}" for r in c.get("career_history", [])[:4])
    return (f"Title: {p.get('current_title')} | {p.get('years_of_experience')} yrs | "
            f"{p.get('location')}, {p.get('country')}\nSummary: {(p.get('summary') or '')[:300]}\n"
            f"History: {hist}\nResponse rate: {sig.get('recruiter_response_rate')} | "
            f"open_to_work: {sig.get('open_to_work_flag')} | relocate: {sig.get('willing_to_relocate')}")

def judge(client, model, c):
    msg = client.messages.create(model=model, max_tokens=5, messages=[{
        "role": "user",
        "content": f"JOB:\n{JD_QUERY}\n\n{RUBRIC}\n\nCANDIDATE:\n{profile_blurb(c)}"}])
    txt = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    for ch in txt:
        if ch in "01234":
            return int(ch)
    return 0

def dcg(rels, k):
    return sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels[:k]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("--model", default="claude-3-5-haiku-20241022")
    args = ap.parse_args()

    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

    cands = [json.loads(l) for l in open(args.candidates, encoding="utf-8") if l.strip()]
    rows = score_candidates(cands)
    by_id = {c["candidate_id"]: c for c in cands}

    # stratified sample: our top 60 + random tail, so the judge sees good and bad
    top_ids = [r["candidate_id"] for r in rows[:60]]
    rest = [r["candidate_id"] for r in rows[60:]]
    random.seed(0)
    sample_ids = top_ids + random.sample(rest, max(0, args.sample - len(top_ids)))

    labels = {}
    for i, cid in enumerate(sample_ids, 1):
        labels[cid] = judge(client, args.model, by_id[cid])
        if i % 25 == 0:
            print(f"  judged {i}/{len(sample_ids)}", file=sys.stderr)
    json.dump(labels, open("eval/llm_labels.json", "w"), indent=1)

    # our ranking restricted to the judged sample, scored against LLM tiers
    judged_order = [r["candidate_id"] for r in rows if r["candidate_id"] in labels]
    rels = [labels[cid] for cid in judged_order]
    ideal = sorted(labels.values(), reverse=True)
    n10 = dcg(rels, 10) / dcg(ideal, 10) if dcg(ideal, 10) else 0
    n50 = dcg(rels, 50) / dcg(ideal, 50) if dcg(ideal, 50) else 0
    print(f"\nIndependent LLM-judge eval on {len(labels)} candidates:")
    print(f"  NDCG@10 = {n10:.3f}")
    print(f"  NDCG@50 = {n50:.3f}")
    print("  (labels saved to eval/llm_labels.json)")

if __name__ == "__main__":
    main()
