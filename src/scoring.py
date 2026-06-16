"""
scoring.py
==========
Fuses the per-candidate features into a single fit score and assembles the
ranked output. Hybrid semantic similarity = TF-IDF (lexical) fused with an
optional precomputed dense matrix (bge-small). If the dense matrix is absent,
the system degrades gracefully to TF-IDF + structured rules (still strong).

All CPU, no network, deterministic.
"""
from __future__ import annotations
from datetime import date

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import jd_spec as J
from . import features as F
from .reasoning import build_reasoning


def _minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def semantic_similarity(docs: list[str], dense: np.ndarray | None,
                        dense_jd: np.ndarray | None) -> np.ndarray:
    """Return per-candidate semantic score in [0,1], fusing lexical + dense."""
    # ---- lexical (TF-IDF) ----
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1, 2),
                          stop_words="english", sublinear_tf=True)
    mat = vec.fit_transform(docs + [J.JD_QUERY])
    cand_mat, jd_vec = mat[:-1], mat[-1]
    lexical = cosine_similarity(cand_mat, jd_vec).ravel()
    lexical = _minmax(lexical)

    if dense is not None and dense_jd is not None:
        # normalize rows then cosine vs jd
        d = dense / (np.linalg.norm(dense, axis=1, keepdims=True) + 1e-9)
        q = dense_jd / (np.linalg.norm(dense_jd) + 1e-9)
        dense_sim = d @ q
        dense_sim = _minmax(dense_sim)
        return 0.5 * lexical + 0.5 * dense_sim
    return lexical


def score_candidates(candidates: list[dict], dense: np.ndarray | None = None,
                     dense_jd: np.ndarray | None = None) -> list[dict]:
    # reference "today" = latest activity in the pool (recency is relative)
    today = date(2025, 1, 1)
    for c in candidates:
        la = c.get("redrob_signals", {}).get("last_active_date")
        if la:
            try:
                d = date.fromisoformat(la)
                if d > today:
                    today = d
            except ValueError:
                pass

    docs = [F.semantic_doc(c) for c in candidates]
    sem = semantic_similarity(docs, dense, dense_jd)

    rows = []
    for i, c in enumerate(candidates):
        honey, hreason = F.is_honeypot(c)

        dom, dom_label = F.domain_score(c)
        ev, ev_hl = F.evidence_score(c)
        exp, yoe = F.experience_score(c)
        loc, loc_label = F.location_score(c)
        pen, pen_notes = F.penalty_multiplier(c)
        beh, beh_notes = F.behavioral_multiplier(c, today)

        comps = {
            "domain": dom, "evidence": ev, "semantic": float(sem[i]),
            "location": loc, "experience": exp,
        }
        base = sum(J.WEIGHTS[k] * comps[k] for k in J.WEIGHTS)
        final = base * pen * beh
        if honey:
            final = 0.0  # force honeypots to the bottom

        flags = {
            "evidence_highlights": ev_hl, "location_label": loc_label,
            "behavioral_notes": beh_notes, "penalty_notes": pen_notes,
            "domain_label": dom_label, "honeypot": honey, "honeypot_reason": hreason,
        }
        rows.append({
            "candidate_id": c["candidate_id"],
            "final": final, "comps": comps, "flags": flags, "cand": c,
        })

    # sort: score desc, then candidate_id asc (validator tie-break rule)
    rows.sort(key=lambda r: (-r["final"], r["candidate_id"]))
    return rows


def build_submission(rows: list[dict], top_n: int = 100) -> list[dict]:
    top = rows[:top_n]
    # Rescale scores into a clean non-increasing band within (0,1].
    finals = np.array([r["final"] for r in top], dtype=float)
    if finals.max() > 0:
        scaled = 0.30 + 0.69 * (finals / finals.max())
    else:
        scaled = np.linspace(0.5, 0.3, len(top))

    staged = []
    for r, sc in zip(top, scaled):
        staged.append({
            "candidate_id": r["candidate_id"],
            "score": round(float(sc), 4),
            "reasoning": build_reasoning(r["cand"], r["comps"], r["flags"], r["final"]),
        })

    # Validator rule: score non-increasing by rank AND, for equal scores,
    # candidate_id strictly ascending. Re-sort the rounded scores to enforce both.
    staged.sort(key=lambda x: (-x["score"], x["candidate_id"]))

    out = []
    for rank, s in enumerate(staged, start=1):
        out.append({
            "candidate_id": s["candidate_id"],
            "rank": rank,
            "score": f"{s['score']:.4f}",
            "reasoning": s["reasoning"],
        })
    return out
