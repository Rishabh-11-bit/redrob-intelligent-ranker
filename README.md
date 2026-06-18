# Redrob — Intelligent Candidate Discovery & Ranking
**🔗 Live demo (sandbox):** https://huggingface.co/spaces/rishh36/redrob-ranker

Ranks the top-100 candidates from a 100K pool for the released Senior AI
Engineer JD — the way a great recruiter would, not by keyword matching.

## TL;DR — reproduce the submission

```bash
pip install -r requirements.txt
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
python validate_submission.py submission.csv      # -> "Submission is valid."
```

Runs in well under the 5-minute / 16 GB / CPU-only / no-network budget.

Optional dense-embedding fusion (recommended; precompute is offline and may
exceed 5 min — the ranking step still does not):

```bash
python precompute_embeddings.py --candidates ./data/candidates.jsonl --out ./artifacts
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv \
  --dense ./artifacts/cand_emb.npy --dense-jd ./artifacts/jd_emb.npy \
  --dense-ids ./artifacts/cand_ids.txt
```

## The core idea

The JD states outright that ranking by "most AI keywords in the skills list" is
a trap built into the data. So the system reasons about the gap between what a
profile **says** and what it **means**:

1. **Title / role coherence (the anti-trap gate).** A non-technical current
   title (HR Manager, Accountant, Marketing Manager, …) is heavily penalized no
   matter how rich the skills list. This alone removes ~70% of the pool
   correctly.
2. **Genuine build-evidence.** Mined from career *descriptions* — never the
   skills array — for real ranking / search / recommendation / retrieval work
   shipped at product companies.
3. **Hybrid semantic similarity.** TF-IDF (lexical) fused with a local
   bge-small dense embedding of the career narrative, so a candidate who built
   a recommender without ever writing "RAG" still surfaces.
4. **Location fit.** India required; Pune/Noida preferred; abroad heavily
   down-weighted (no visa sponsorship per the JD).
5. **Soft experience band** around 6–8 years.

Two multipliers modify the base:

- **Disqualifier penalty** — services-only career, title-chaser tenure,
  vision/speech-only without NLP/IR, research-only without production.
- **Behavioral availability** — recruiter response rate, recency, open-to-work,
  interview completion, notice period. An unavailable "perfect-on-paper"
  candidate is down-weighted, exactly as the JD demands.

**Honeypots** with impossible profiles (e.g., a single role longer than the
whole career, "expert" skills with 0 months used, current role with an end
date) are detected and forced to the bottom — keeping the top-100 honeypot rate
at 0% (DQ threshold is >10%).

The `reasoning` column is assembled deterministically from each candidate's
real fields, so it is specific, non-hallucinated, and consistent with the rank.

## Layout

```
rank.py                     single-command ranker (entrypoint)
precompute_embeddings.py    offline dense embeddings (bge-small-en-v1.5)
app.py                      Streamlit sandbox (spec Section 10.5)
src/
  jd_spec.py                hand-encoded JD requirements, lexicons, weights
  features.py               title coherence, evidence, disqualifiers,
                            location, experience, behavioral, honeypot
  scoring.py                hybrid semantic + fusion + submission assembly
  reasoning.py              deterministic, fact-grounded reasoning strings
eval/
  evaluate.py               local silver-metric proxy + DQ guardrail checks
data/candidates.jsonl       input pool
submission_metadata.yaml    portal metadata mirror
```

## Local validation

No public leaderboard and only 3 submissions, so validate locally:

```bash
python eval/evaluate.py --candidates ./data/candidates.jsonl --submission ./submission.csv
```

This reports silver NDCG/MAP/P@10 (a proxy — track *movement* across iterations,
not the absolute value) and non-circular guardrail checks tied to the DQ rules.
