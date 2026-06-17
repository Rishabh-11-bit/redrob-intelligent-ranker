# Reproduces the RANKING step exactly: CPU-only, offline, <5 min.
# Dense embeddings are precomputed offline (see precompute_embeddings.py) and,
# if present under ./artifacts, are fused automatically.
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir "numpy>=1.24" "scikit-learn>=1.3"
COPY . .
# build:  docker build -t redrob-ranker .
# run:    docker run --rm --network none -v "$PWD/data:/app/data" \
#                  -v "$PWD/out:/app/out" redrob-ranker
CMD ["python", "rank.py", "--candidates", "./data/candidates.jsonl", "--out", "./out/submission.csv"]
