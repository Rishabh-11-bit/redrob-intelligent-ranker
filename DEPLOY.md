# Deploy & reproduce

## A. One-command reproduction (Docker — satisfies spec §10.5 without a hosted host)
```bash
docker build -t redrob-ranker .
mkdir -p out
docker run --rm --network none -v "$PWD/data:/app/data" -v "$PWD/out:/app/out" redrob-ranker
python validate_submission.py out/submission.csv
```
`--network none` proves the ranking step needs no internet.

## B. Hosted sandbox — HuggingFace Spaces (free)
1. Create a new Space → SDK: **Streamlit**.
2. Push this repo to the Space (or connect the GitHub repo).
3. Space settings: `app_file = app.py`; add a `requirements.txt` with
   `streamlit`, `numpy`, `scikit-learn`.
4. The Space accepts a ≤100-candidate JSONL/JSON upload and returns a ranked CSV.

## C. Optional dense fusion (run once on your machine, then rank)
```bash
python precompute_embeddings.py --candidates ./data/candidates.jsonl --out ./artifacts
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv \
  --dense ./artifacts/cand_emb.npy --dense-jd ./artifacts/jd_emb.npy \
  --dense-ids ./artifacts/cand_ids.txt
```
