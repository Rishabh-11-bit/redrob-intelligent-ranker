"""
features.py
===========
Pure-Python, deterministic feature extraction for one candidate.
No network, no LLM, CPU-only. Every function returns numbers the scorer
fuses, plus structured flags the reasoning module turns into plain language.
"""
from __future__ import annotations
from datetime import date
from typing import Any

from . import jd_spec as J


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _lc(s: Any) -> str:
    return (s or "").lower() if isinstance(s, str) else ""


def _any_in(text: str, terms: list[str]) -> bool:
    return any(t in text for t in terms)


def _count_terms(text: str, terms: list[str]) -> int:
    return sum(1 for t in terms if t in text)


def career_text(c: dict) -> str:
    """Concatenated career NARRATIVE (titles + descriptions + industries).
    Deliberately excludes the skills[].name list — the skills list is where
    the keyword-stuffing trap lives."""
    parts = [_lc(c["profile"].get("headline")), _lc(c["profile"].get("summary"))]
    for r in c.get("career_history", []):
        parts.append(_lc(r.get("title")))
        parts.append(_lc(r.get("description")))
        parts.append(_lc(r.get("industry")))
    return " ".join(parts)


def semantic_doc(c: dict) -> str:
    """Document text fed to TF-IDF / dense embedding. Career narrative only."""
    return career_text(c)


# ---------------------------------------------------------------------------
# 1. Title / role coherence  -> [0, 1]
# ---------------------------------------------------------------------------
def domain_score(c: dict) -> tuple[float, str]:
    cur = _lc(c["profile"].get("current_title"))
    hist = [_lc(r.get("title")) for r in c.get("career_history", [])]

    def bucket(title: str) -> str:
        if _any_in(title, J.CORE_AI_TITLES):
            return "core"
        if _any_in(title, J.ADJACENT_TECH_TITLES):
            return "adjacent"
        if _any_in(title, J.NON_TECH_TITLES):
            return "nontech"
        return "unknown"

    cur_b = bucket(cur)
    hist_b = [bucket(t) for t in hist]

    # Best signal across current + history, but current title weighted most.
    if cur_b == "core":
        score, label = 1.0, "core AI/ML role"
    elif cur_b == "adjacent":
        # adjacent title is a fit only if history shows core or build evidence;
        # base credit given, evidence component lifts it further.
        score, label = 0.62, "adjacent technical role"
        if "core" in hist_b:
            score, label = 0.78, "technical role with prior ML/AI history"
    elif cur_b == "nontech":
        # The trap. Heavy penalty even if history has a tech blip.
        score, label = 0.06, "non-technical role (skills-list mismatch)"
        if "core" in hist_b:
            score, label = 0.30, "currently non-technical, some prior tech history"
    else:  # unknown current title
        if "core" in hist_b:
            score, label = 0.55, "unclear title, prior core ML/AI history"
        elif "adjacent" in hist_b:
            score, label = 0.40, "unclear title, prior technical history"
        else:
            score, label = 0.12, "no clear technical role history"
    return score, label


# ---------------------------------------------------------------------------
# 2. Genuine build evidence  -> [0, 1]
# ---------------------------------------------------------------------------
def evidence_score(c: dict) -> tuple[float, list[str]]:
    txt = career_text(c)
    matched = [t for t in J.BUILD_EVIDENCE_TERMS if t in txt]
    strong = [t for t in J.BUILD_EVIDENCE_STRONG if t in txt]
    prod = _count_terms(txt, J.PRODUCTION_TERMS)

    # diminishing returns; strong terms count double
    raw = len(matched) + len(strong)
    base = min(1.0, raw / 6.0)
    prod_boost = min(0.15, 0.05 * prod)
    score = min(1.0, base * 0.85 + prod_boost)
    # de-dup human-readable list of the strongest evidence found
    highlights = strong[:3] if strong else matched[:3]
    return score, highlights


# ---------------------------------------------------------------------------
# 3. Experience fit  -> [0, 1]  (soft band around 6-8 yrs)
# ---------------------------------------------------------------------------
def experience_score(c: dict) -> tuple[float, float]:
    y = float(c["profile"].get("years_of_experience", 0) or 0)
    if J.EXP_IDEAL_LOW <= y <= J.EXP_IDEAL_HIGH:
        s = 1.0
    elif J.EXP_BAND_LOW <= y <= J.EXP_BAND_HIGH:
        s = 0.85
    elif 3 <= y < J.EXP_BAND_LOW or J.EXP_BAND_HIGH < y <= 12:
        s = 0.55
    else:
        s = 0.30
    return s, y


# ---------------------------------------------------------------------------
# 4. Location fit  -> [0, 1]   (India requirement; no visa sponsorship abroad)
# ---------------------------------------------------------------------------
def location_score(c: dict) -> tuple[float, str]:
    p = c["profile"]
    country = _lc(p.get("country"))
    loc = _lc(p.get("location"))
    relo = bool(c.get("redrob_signals", {}).get("willing_to_relocate", False))

    if country == "india":
        if _any_in(loc, J.PREFERRED_CITIES):
            return 1.0, "Pune/Noida-based"
        if _any_in(loc, J.TIER1_INDIA_CITIES):
            return 0.92, "Tier-1 Indian city"
        return (0.72, "India, open to relocate") if relo else (0.55, "India, non-Tier-1")
    # outside India: case-by-case, no visa sponsorship
    return (0.35, "outside India, willing to relocate") if relo else (0.12, "outside India (no visa sponsorship)")


# ---------------------------------------------------------------------------
# 5. Disqualifier penalty multiplier  -> ~[0.3, 1.0]
# ---------------------------------------------------------------------------
def penalty_multiplier(c: dict) -> tuple[float, list[str]]:
    txt = career_text(c)
    notes: list[str] = []
    mult = 1.0

    companies = [_lc(r.get("company")) for r in c.get("career_history", [])]
    # services-only career (no product company anywhere)
    if companies and all(_any_in(co, J.SERVICES_COMPANIES) for co in companies):
        mult *= 0.45
        notes.append("services-only career")
    elif companies and _any_in(_lc(c["profile"].get("current_company")), J.SERVICES_COMPANIES) \
            and any(not _any_in(co, J.SERVICES_COMPANIES) for co in companies):
        notes.append("currently at services firm but has product-company history")

    # title-chaser: >=3 roles, average tenure < 18 months
    hist = c.get("career_history", [])
    if len(hist) >= 3:
        durs = [r.get("duration_months", 0) or 0 for r in hist]
        if durs and (sum(durs) / len(durs)) < 18:
            mult *= 0.7
            notes.append("short average tenure (title-chaser pattern)")

    # CV/speech/robotics primary without NLP/IR
    cv = _count_terms(txt, J.CV_SPEECH_ROBOTICS_TERMS)
    ir = _count_terms(txt, J.NLP_IR_TERMS)
    if cv >= 2 and ir == 0:
        mult *= 0.6
        notes.append("vision/speech/robotics focus, no NLP/IR exposure")

    # research-only with no production
    if _any_in(txt, J.RESEARCH_ONLY_TERMS) and not _any_in(txt, J.PRODUCTION_TERMS):
        mult *= 0.6
        notes.append("research-only, no production deployment signal")

    return mult, notes


# ---------------------------------------------------------------------------
# 6. Behavioral availability multiplier  -> [0.5, 1.15]
#    "A perfect-on-paper candidate who hasn't logged in for 6 months and has a
#     5% response rate is, for hiring purposes, not actually available."
# ---------------------------------------------------------------------------
def behavioral_multiplier(c: dict, today: date) -> tuple[float, list[str]]:
    s = c.get("redrob_signals", {})
    m = 1.0
    notes: list[str] = []

    rr = float(s.get("recruiter_response_rate", 0) or 0)
    if rr < 0.10:
        m *= 0.70; notes.append(f"low recruiter response rate ({rr:.0%})")
    elif rr >= 0.50:
        m *= 1.08; notes.append(f"responsive to recruiters ({rr:.0%})")

    # recency
    la = s.get("last_active_date")
    if la:
        try:
            d = date.fromisoformat(la)
            days = (today - d).days
            if days > 180:
                m *= 0.70; notes.append(f"inactive {days} days")
            elif days <= 14:
                m *= 1.05; notes.append("recently active")
        except ValueError:
            pass

    if s.get("open_to_work_flag"):
        m *= 1.06; notes.append("open to work")
    else:
        m *= 0.96

    icr = s.get("interview_completion_rate")
    if icr is not None and icr >= 0 and icr < 0.4:
        m *= 0.85; notes.append("low interview completion")

    npd = s.get("notice_period_days")
    if npd is not None:
        if npd <= 30:
            m *= 1.04; notes.append(f"{npd}-day notice")
        elif npd > 60:
            m *= 0.94; notes.append(f"{npd}-day notice (long)")

    saved = s.get("saved_by_recruiters_30d", 0) or 0
    if saved >= 5:
        m *= 1.03

    m = max(0.5, min(1.15, m))
    return m, notes


# ---------------------------------------------------------------------------
# 7. Honeypot detector. Subtly impossible profiles -> force to bottom.
#    Honeypot rate > 10% in top 100 = disqualification, so be strict.
# ---------------------------------------------------------------------------
def is_honeypot(c: dict) -> tuple[bool, str]:
    p = c["profile"]
    yoe = float(p.get("years_of_experience", 0) or 0)
    hist = c.get("career_history", [])

    # (a) total career duration wildly exceeds claimed years of experience
    total_months = sum(r.get("duration_months", 0) or 0 for r in hist)
    # allow generous overlap slack of 18 months
    if total_months > (yoe * 12) + 18 and yoe > 0:
        # could be parallel roles; only flag if a SINGLE role already exceeds yoe
        if any((r.get("duration_months", 0) or 0) > yoe * 12 + 12 for r in hist):
            return True, "single role longer than total career"

    # (b) a role at a company longer than the company could plausibly exist:
    #     start_date earlier than 1990 or after end_date
    for r in hist:
        sd, ed = r.get("start_date"), r.get("end_date")
        try:
            if sd:
                sdate = date.fromisoformat(sd)
                if ed:
                    edate = date.fromisoformat(ed)
                    if edate < sdate:
                        return True, "role end date before start date"
                if sdate.year < 1985:
                    return True, "implausible start year"
        except (ValueError, TypeError):
            pass

    # (c) "expert" proficiency with 0 months of use (impossible mastery)
    expert_zero = sum(
        1 for sk in c.get("skills", [])
        if sk.get("proficiency") == "expert" and (sk.get("duration_months", 0) or 0) == 0
    )
    if expert_zero >= 2:
        return True, "multiple 'expert' skills with zero months used"

    # (d) a skill used longer than the whole career
    for sk in c.get("skills", []):
        if (sk.get("duration_months", 0) or 0) > (yoe * 12) + 24 and yoe > 0:
            return True, "skill duration exceeds career length"

    # (e) is_current True but an end_date is set
    for r in hist:
        if r.get("is_current") and r.get("end_date"):
            return True, "current role has an end date"

    return False, ""
