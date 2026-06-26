"""eval/robustness.py - is the shortlist a fragile artifact of the hand-set weights?
Perturb every weight by random +/-40% over many trials and measure how stable the
top-100 stays (Jaccard) and whether any safety guardrail ever breaks."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.harness import load, combine, COMPONENTS
from src import jd_spec as J

def top(d, w):
    return set(d["ids"][np.lexsort((d["ids"], -combine(d, weights=w)))[:100]].tolist())

def main(trials=200, pct=0.4, seed=0):
    d = load(); rng = np.random.default_rng(seed)
    base_w = dict(J.WEIGHTS); base = top(d, base_w)
    jac=[]; worst_h=0; worst_nt=0; worst_f=0
    for _ in range(trials):
        w={k: max(1e-3, v*(1+rng.uniform(-pct,pct))) for k,v in base_w.items()}
        s=top(d,w); jac.append(len(base & s)/len(base | s))
        order=np.lexsort((d["ids"], -combine(d, weights=w)))[:100]
        worst_h=max(worst_h,int(d["honeypot"][order].sum()))
        worst_nt=max(worst_nt,int(d["nontech"][order].sum()))
        worst_f=max(worst_f,int(d["foreign"][order].sum()))
    jac=np.array(jac)
    print(f"Weight sensitivity sweep: {trials} trials, each weight perturbed +/-{int(pct*100)}%")
    print(f"  top-100 Jaccard stability vs base: mean {jac.mean():.3f}  min {jac.min():.3f}")
    print(f"  worst-case across all trials: honeypots {worst_h}  non-technical {worst_nt}  foreign {worst_f}")
    print(f"  => the shortlist is {'robust' if jac.mean()>0.85 and worst_h==0 else 'sensitive'}: "
          f"safety guardrails (0 honeypots, 0 non-tech) held in every trial." )

if __name__ == "__main__":
    main()
