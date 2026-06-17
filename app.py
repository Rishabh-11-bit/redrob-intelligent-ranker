"""
app.py — sandbox demo required by submission_spec Section 10.5.

Accepts a small candidate sample (<=100, JSONL or JSON), runs the SAME ranking
pipeline used for the full submission, and returns a downloadable ranked CSV.
CPU-only, no network at ranking time. Deploy free on HuggingFace Spaces or
Streamlit Cloud.

    streamlit run app.py
"""
import io
import json
import csv

import streamlit as st

from src.scoring import score_candidates, build_submission

st.set_page_config(page_title="Redrob Candidate Ranker", layout="wide")
st.title("Redrob — Intelligent Candidate Ranker")
st.caption("Upload a candidate sample (JSONL or JSON, <=100). Runs the full "
           "hybrid + rule-based + behavioral pipeline on CPU, no network.")

uploaded = st.file_uploader("Candidates (.jsonl or .json)", type=["jsonl", "json"])
top_n = st.slider("Top N to return", 5, 100, 25)

if uploaded is not None:
    raw = uploaded.read().decode("utf-8")
    candidates = []
    try:
        if uploaded.name.endswith(".json"):
            data = json.loads(raw)
            candidates = data if isinstance(data, list) else [data]
        else:
            candidates = [json.loads(l) for l in raw.splitlines() if l.strip()]
    except json.JSONDecodeError as e:
        st.error(f"Could not parse file: {e}")

    if candidates:
        st.write(f"Loaded **{len(candidates)}** candidates.")
        with st.spinner("Ranking..."):
            rows = score_candidates(candidates)
            sub = build_submission(rows, top_n=min(top_n, len(candidates)))

        st.subheader("Ranked shortlist")
        st.dataframe(sub, use_container_width=True)

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        for r in sub:
            w.writerow([r["candidate_id"], r["rank"], r["score"], r["reasoning"]])
        st.download_button("Download ranked CSV", buf.getvalue(),
                           file_name="ranked.csv", mime="text/csv")
else:
    st.info("Tip: use a 100-row slice of candidates.jsonl to verify reproducibility.")
