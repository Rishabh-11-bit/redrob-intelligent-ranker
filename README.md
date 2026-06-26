# Redrob — Intelligent Candidate Discovery & Ranking

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

## Evaluation, ablation & fairness

No public leaderboard and only 3 submissions, so the system is validated three
independent ways. All three are reproducible (`eval/`).

### 1. Ablation — does every component earn its place?
`python eval/ablation.py --candidates ./data/candidates.jsonl` switches off one
part at a time and measures the effect. The honeypot / non-tech / top-100-change
columns are objective (not rubric-derived):

```
configuration               NDCG@10  NDCG@50  honeypots non-tech  top100 chg
FULL system                   1.000    0.984          0        0           -
- honeypot kill-switch        0.934    0.848         27        0          27
- behavioral multiplier       0.961    0.962          0        0          17
- disqualifier penalty        1.000    0.991          0        0           3
- role/title gate             1.000    0.991          0        0           7
- credibility                 1.000    0.992          0        0           4
- semantic (hybrid)           1.000    0.992          0        0          10
- build evidence              1.000    0.984          0        0          18
- location fit                0.888    0.932          0        0          12
```
Headline: removing the honeypot gate puts **27 honeypots into the top 100**
(an automatic disqualification), and **location fit drives the largest quality
swing**. Every component changes top-100 membership, so none is dead weight; the
quality signals are also mutually reinforcing (defense-in-depth).

### 2. Independent LLM-judge — is it actually good (non-circular)?
The built-in silver rubric shares assumptions with the ranker, so it only
catches regressions. `eval/llm_judge.py` removes that circularity: an LLM that
never saw the scoring logic tier-labels a stratified sample from the JD, and we
score our ranking against those labels with NDCG. Dev-time only (network + key);
never part of the offline ranking step.

### 3. Fairness & bias audit
`python eval/fairness_audit.py` confirms and discloses:
- **Name / gender / age blind:** the dataset has no gender/age/race fields, the
  only name is anonymised, and the scorer reads no protected attribute.
- **Pedigree-blind:** education tier is deliberately excluded from scoring. A
  residual tier-1 concentration remains in the shortlist, but it is correlation
  in the talent pool, not a ranking choice - measured and disclosed, not hidden.
- **Location skew** (India) is a stated work-authorisation business rule from the
  JD (no visa sponsorship), not a demographic signal.
