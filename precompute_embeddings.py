#!/usr/bin/env python3
"""
precompute_embeddings.py — OFFLINE precompute step (run once).

Generates dense embeddings for every candidate's career narrative and for the
JD query using a small, CPU-friendly sentence-transformer (bge-small-en-v1.5,
384-dim). This step may exceed the 5-minute budget — that's allowed; it is NOT
the ranking step. It writes artifacts that rank.py then fuses at ranking time.

    python precompute_embeddings.py --candidates ./data/candidates.jsonl --out ./artifacts

Outputs:
    artifacts/cand_emb.npy   (N x 384 float32)
    artifacts/jd_emb.npy     (384,)
    artifacts/cand_ids.txt   (candidate_id order, one per line)

Why bge-small-en-v1.5:
    Strong MTEB retrieval quality for its size, runs fine on CPU, ~130MB on
    disk. Swap to bge-base for a quality bump if your machine has the headroom.
    The model weights are bundled/cached locally so the RANKING step stays
    fully offline.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np

from src.features import semantic_doc
from src.jd_spec import JD_QUERY

MODEL_NAME = "BAAI/bge-small-en-v1.5"
# bge models recommend a short instruction prefix on the QUERY side only.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="./artifacts")
    ap.add_argument("--model", default=MODEL_NAME)
    ap.add_argument("--batch-size", type=int, default=256)
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    candidates = []
    with open(args.candidates, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))

    docs = [semantic_doc(c) for c in candidates]
    ids = [c["candidate_id"] for c in candidates]

    model = SentenceTransformer(args.model)
    print(f"[precompute] embedding {len(docs):,} candidates with {args.model}")
    emb = model.encode(docs, batch_size=args.batch_size, show_progress_bar=True,
                       normalize_embeddings=True).astype("float32")
    jd = model.encode([QUERY_PREFIX + JD_QUERY], normalize_embeddings=True).astype("float32")[0]

    np.save(out / "cand_emb.npy", emb)
    np.save(out / "jd_emb.npy", jd)
    (out / "cand_ids.txt").write_text("\n".join(ids), encoding="utf-8")
    print(f"[precompute] wrote artifacts to {out}/  (cand_emb {emb.shape})")


if __name__ == "__main__":
    main()
