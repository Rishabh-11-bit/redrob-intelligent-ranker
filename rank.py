#!/usr/bin/env python3
"""
rank.py — produce the top-100 ranked submission CSV from candidates.jsonl.

Single-command, CPU-only, no network. Optionally fuses a precomputed dense
embedding matrix (see precompute_embeddings.py); if absent, runs the hybrid
TF-IDF + structured-rule pipeline alone.

    python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
    python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv \
                   --dense ./artifacts/cand_emb.npy --dense-jd ./artifacts/jd_emb.npy
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

from src.scoring import score_candidates, build_submission


def load_candidates(path: str) -> list[dict]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Redrob candidate ranker")
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="submission.csv")
    ap.add_argument("--dense", default=None, help="precomputed candidate embeddings .npy")
    ap.add_argument("--dense-jd", default=None, help="precomputed JD embedding .npy")
    ap.add_argument("--dense-ids", default=None, help="candidate_id order for dense .npy")
    ap.add_argument("--top", type=int, default=100)
    args = ap.parse_args()

    t0 = time.time()
    candidates = load_candidates(args.candidates)
    print(f"[rank] loaded {len(candidates):,} candidates", file=sys.stderr)

    dense = dense_jd = None
    if args.dense and args.dense_jd and Path(args.dense).exists():
        dense = np.load(args.dense)
        dense_jd = np.load(args.dense_jd).ravel()
        # align dense rows to candidate order if an id file is provided
        if args.dense_ids and Path(args.dense_ids).exists():
            order = [l.strip() for l in open(args.dense_ids) if l.strip()]
            pos = {cid: i for i, cid in enumerate(order)}
            idx = [pos[c["candidate_id"]] for c in candidates]
            dense = dense[idx]
        print(f"[rank] fusing dense embeddings {dense.shape}", file=sys.stderr)

    rows = score_candidates(candidates, dense=dense, dense_jd=dense_jd)
    submission = build_submission(rows, top_n=args.top)

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        for r in submission:
            w.writerow([r["candidate_id"], r["rank"], r["score"], r["reasoning"]])

    print(f"[rank] wrote {len(submission)} rows to {args.out} "
          f"in {time.time() - t0:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
