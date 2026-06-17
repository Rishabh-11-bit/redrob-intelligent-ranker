#!/usr/bin/env python3
"""
precompute_embeddings.py — OFFLINE precompute (run once).

Two-stage design so it finishes in minutes on a CPU instead of hours:

  Stage 1  the fast TF-IDF + rules + behavioral pipeline ranks all 100K.
  Stage 2  ONLY the top-K shortlist is embedded with bge-small (dense). Only
           candidates near the top can change the final top-100, so embedding
           the long tail is wasted compute. Non-shortlisted candidates get a
           zero dense vector. This mirrors real retrieve-then-rerank systems.

Outputs (consumed unchanged by rank.py):
  artifacts/cand_emb.npy   (N x 384; real rows for the shortlist, zeros elsewhere)
  artifacts/jd_emb.npy     (384,)
  artifacts/cand_ids.txt   (full candidate_id order)

Tune --rerank-topk lower (e.g. 1500) for an even faster run.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

import numpy as np

from src.features import semantic_doc
from src.jd_spec import JD_QUERY
from src.scoring import score_candidates

MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="./artifacts")
    ap.add_argument("--model", default=MODEL_NAME)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--rerank-topk", type=int, default=3000,
                    help="embed only the top-K from the fast first stage")
    ap.add_argument("--max-seq-len", type=int, default=256,
                    help="truncate candidate text to this many tokens (lower = faster)")
    args = ap.parse_args()

    import torch
    from sentence_transformers import SentenceTransformer
    try:
        torch.set_num_threads(os.cpu_count() or 4)
    except Exception:
        pass

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    candidates = []
    with open(args.candidates, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))
    ids = [c["candidate_id"] for c in candidates]
    pos = {cid: i for i, cid in enumerate(ids)}
    print(f"[precompute] {len(candidates):,} candidates loaded")

    # ---- Stage 1: fast ranking picks the shortlist worth embedding ----
    rows = score_candidates(candidates)  # no dense
    k = min(args.rerank_topk, len(rows))
    shortlist_pos = [pos[r["candidate_id"]] for r in rows[:k]]
    print(f"[precompute] dense-embedding only the top {k:,} (retrieve-then-rerank)")

    docs = [semantic_doc(candidates[i]) for i in shortlist_pos]

    model = SentenceTransformer(args.model)
    model.max_seq_length = args.max_seq_len
    emb_short = model.encode(docs, batch_size=args.batch_size, show_progress_bar=True,
                             normalize_embeddings=True).astype("float32")
    dim = emb_short.shape[1]

    cand_emb = np.zeros((len(candidates), dim), dtype="float32")
    for vec, p in zip(emb_short, shortlist_pos):
        cand_emb[p] = vec

    jd = model.encode([QUERY_PREFIX + JD_QUERY], normalize_embeddings=True).astype("float32")[0]

    np.save(out / "cand_emb.npy", cand_emb)
    np.save(out / "jd_emb.npy", jd)
    (out / "cand_ids.txt").write_text("\n".join(ids), encoding="utf-8")
    print(f"[precompute] wrote artifacts to {out}/  "
          f"(cand_emb {cand_emb.shape}, {k} real rows)")


if __name__ == "__main__":
    main()
