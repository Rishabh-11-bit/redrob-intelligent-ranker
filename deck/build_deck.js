const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

// ---------- palette ----------
const NAVY = "0F2A3F";      // deep navy-teal (dark slides)
const NAVY2 = "163b54";     // panel on dark
const TEAL = "0D9488";      // primary accent
const TEAL_L = "2DD4BF";    // light accent
const INK = "1E293B";       // body text on light
const MUTED = "64748B";     // muted labels
const CARD = "F1F5F9";      // light card tint
const CARDTEAL = "ECFDF8";  // teal-tinted card
const WHITE = "FFFFFF";
const RED = "DC2626";

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Comp, { color, size: String(size) })
  );
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}
const shadow = () => ({ type: "outer", color: "000000", blur: 7, offset: 3, angle: 90, opacity: 0.12 });

(async () => {
  const p = new pptxgen();
  p.layout = "LAYOUT_WIDE";        // 13.3 x 7.5
  p.author = "Rishabh Gaikwad";
  p.title = "Redrob Intelligent Candidate Ranker";
  const W = 13.3;

  // preload icons
  const ic = {
    target: await icon(FA.FaBullseye, "#" + TEAL_L),
    trap: await icon(FA.FaExclamationTriangle, "#FBBF24"),
    brain: await icon(FA.FaBrain, "#" + TEAL),
    layers: await icon(FA.FaLayerGroup, "#" + TEAL),
    bolt: await icon(FA.FaBolt, "#" + TEAL),
    shield: await icon(FA.FaShieldAlt, "#" + TEAL),
    check: await icon(FA.FaCheckCircle, "#" + TEAL),
    x: await icon(FA.FaTimesCircle, "#" + RED),
    map: await icon(FA.FaMapMarkerAlt, "#" + TEAL),
    code: await icon(FA.FaCode, "#" + TEAL),
    chart: await icon(FA.FaChartLine, "#" + TEAL),
    user: await icon(FA.FaUserCheck, "#" + TEAL_L),
    gear: await icon(FA.FaCogs, "#" + TEAL),
    search: await icon(FA.FaSearch, "#" + TEAL),
    file: await icon(FA.FaFileCsv, "#" + TEAL),
  };

  const pageNum = (s, n) =>
    s.addText(`${n}`, { x: W - 0.7, y: 7.0, w: 0.4, h: 0.3, fontSize: 10, color: MUTED, align: "right", fontFace: "Arial" });

  // ============================================================= 1 TITLE
  let s = p.addSlide();
  s.background = { color: NAVY };
  s.addImage({ data: ic.target, x: 0.7, y: 0.85, w: 0.7, h: 0.7 });
  s.addText("REDROB · DATA & AI CHALLENGE", {
    x: 1.55, y: 0.9, w: 9, h: 0.6, fontSize: 15, color: TEAL_L, bold: true, charSpacing: 3, fontFace: "Arial", valign: "middle"
  });
  s.addText("Reading Between the Lines", {
    x: 0.7, y: 2.2, w: 11.9, h: 1.1, fontSize: 50, bold: true, color: WHITE, fontFace: "Cambria"
  });
  s.addText("A recruiter-grade candidate ranker that understands fit — not keywords", {
    x: 0.72, y: 3.35, w: 11.5, h: 0.7, fontSize: 21, color: "CADCFC", fontFace: "Arial"
  });
  s.addText([
    { text: "Hybrid retrieval", options: { color: TEAL_L, bold: true } },
    { text: "  +  rule-based fit gating  +  behavioral availability  +  honeypot defense", options: { color: "9FB3C8" } },
  ], { x: 0.72, y: 4.25, w: 11.5, h: 0.5, fontSize: 15, fontFace: "Arial" });
  s.addText([
    { text: "Rishabh Gaikwad", options: { bold: true, color: WHITE } },
    { text: "   ·   100,000-candidate pool   ·   CPU-only, offline, < 1 min", options: { color: "9FB3C8" } },
  ], { x: 0.72, y: 6.3, w: 11.5, h: 0.4, fontSize: 14, fontFace: "Arial" });

  // ============================================================= 2 PROBLEM
  s = p.addSlide();
  s.background = { color: WHITE };
  s.addText("The problem keyword filters can't solve", {
    x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria"
  });
  s.addText("The brief says it plainly: recruiters miss the right person because filters match words, not meaning. This dataset weaponizes that.", {
    x: 0.72, y: 1.25, w: 11.8, h: 0.6, fontSize: 16, color: MUTED, fontFace: "Arial" });

  const probCards = [
    { ic: ic.trap, t: "The keyword trap", d: "An HR Manager can list 9 AI skills. A pure-embedding ranker puts them at #1. The JD says this is a trap built into the data on purpose." },
    { ic: ic.x, t: "Honeypots", d: "~80 profiles are subtly impossible (8 yrs at a 3-yr-old firm). Rank them in your top 10 and you signal you never read the profile." },
    { ic: ic.user, t: "Availability ≠ paper fit", d: "A perfect resume that's been inactive 6 months with a 5% response rate is, for hiring, not actually available." },
  ];
  probCards.forEach((c, i) => {
    const x = 0.7 + i * 4.05;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.15, w: 3.75, h: 3.5, fill: { color: CARD }, rectRadius: 0.12, shadow: shadow() });
    s.addImage({ data: c.ic, x: x + 0.35, y: 2.5, w: 0.6, h: 0.6 });
    s.addText(c.t, { x: x + 0.32, y: 3.25, w: 3.1, h: 0.5, fontSize: 19, bold: true, color: INK, fontFace: "Arial" });
    s.addText(c.d, { x: x + 0.32, y: 3.85, w: 3.15, h: 1.7, fontSize: 13.5, color: "475569", fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.05 });
  });
  s.addText([
    { text: "Right answer (from the JD): ", options: { bold: true, color: TEAL } },
    { text: "reason about the gap between what a profile says and what it means.", options: { color: INK } },
  ], { x: 0.7, y: 6.0, w: 11.9, h: 0.5, fontSize: 15.5, fontFace: "Arial" });
  pageNum(s, 2);

  // ============================================================= 3 DATA AUDIT
  s = p.addSlide();
  s.background = { color: WHITE };
  s.addText("What the 100K pool actually looks like", {
    x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria" });
  s.addText("I profiled the full dataset before designing anything. The shape of the pool dictates the architecture.", {
    x: 0.72, y: 1.25, w: 11.8, h: 0.5, fontSize: 16, color: MUTED, fontFace: "Arial" });

  // stat callouts (left)
  const stats = [
    { n: "100K", l: "candidate profiles" },
    { n: "75%", l: "India-based (25% abroad, no visa sponsorship)" },
    { n: "~70%", l: "non-technical job titles" },
    { n: "~80", l: "honeypot profiles (DQ if >10% of top 100)" },
  ];
  stats.forEach((st, i) => {
    const y = 2.1 + i * 1.15;
    s.addText(st.n, { x: 0.7, y, w: 2.0, h: 0.9, fontSize: 40, bold: true, color: TEAL, fontFace: "Cambria", align: "left", valign: "middle" });
    s.addText(st.l, { x: 2.75, y, w: 3.2, h: 0.9, fontSize: 13.5, color: "475569", fontFace: "Arial", valign: "middle" });
  });

  // chart (right): pool composition by role family
  s.addText("Pool by role family", { x: 6.6, y: 1.95, w: 6, h: 0.4, fontSize: 15, bold: true, color: INK, fontFace: "Arial" });
  s.addChart(p.charts.BAR, [{
    name: "share", labels: ["Non-technical roles", "Software / other eng", "Core AI / ML / Search"], values: [70, 24, 6]
  }], {
    x: 6.5, y: 2.3, w: 6.2, h: 3.6, barDir: "bar",
    chartColors: [TEAL], chartColorsOpacity: [100],
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFormatCode: '0"%"',
    catAxisLabelColor: "475569", catAxisLabelFontSize: 12,
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: false, valAxisMaxVal: 80,
  });
  s.addText("The genuine target — core AI/ML engineers in India — is a thin 6% sliver. The JD agrees: \"10 great matches beat 1000 maybes.\"", {
    x: 0.7, y: 6.55, w: 12, h: 0.5, fontSize: 14, italic: true, color: MUTED, fontFace: "Arial" });
  pageNum(s, 3);

  // ============================================================= 4 INSIGHT
  s = p.addSlide();
  s.background = { color: WHITE };
  s.addText("The decisive design choice", {
    x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria" });
  s.addText([
    { text: "Embed what a candidate ", options: { color: MUTED } },
    { text: "did", options: { bold: true, color: TEAL } },
    { text: " (career descriptions) — never what they ", options: { color: MUTED } },
    { text: "listed", options: { bold: true, color: RED } },
    { text: " (the skills array, where the trap lives).", options: { color: MUTED } },
  ], { x: 0.72, y: 1.25, w: 11.8, h: 0.5, fontSize: 16, fontFace: "Arial" });

  // two contrast cards
  const trapCard = { x: 0.7, head: "Looks perfect, scored low", col: RED, icon: ic.x,
    rows: ["Title: Marketing Manager", "Skills: 9 AI keywords, all \"expert\"", "Career text: campaigns, brand, GTM", "→ no ranking / retrieval work ever shipped"], verdict: "Role-coherence gate kills it." };
  const fitCard = { x: 6.85, head: "No buzzwords, scored high", col: TEAL, icon: ic.check,
    rows: ["Title: Backend / Platform Engineer", "Skills: modest, honestly rated", "Career text: built a recommendation", "    + search-ranking system at a product co"], verdict: "Build-evidence + semantics surface it." };
  [trapCard, fitCard].forEach((c) => {
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: c.x, y: 2.1, w: 5.75, h: 3.6, fill: { color: c.col === RED ? "FEF2F2" : CARDTEAL }, rectRadius: 0.12, shadow: shadow() });
    s.addImage({ data: c.icon, x: c.x + 0.35, y: 2.4, w: 0.5, h: 0.5 });
    s.addText(c.head, { x: c.x + 1.0, y: 2.4, w: 4.5, h: 0.5, fontSize: 18, bold: true, color: c.col, fontFace: "Arial", valign: "middle" });
    s.addText(c.rows.map((r, i) => ({ text: r, options: { breakLine: true, bullet: false, color: INK } })),
      { x: c.x + 0.4, y: 3.15, w: 5.0, h: 1.8, fontSize: 14, fontFace: "Arial", lineSpacingMultiple: 1.25, valign: "top" });
    s.addText(c.verdict, { x: c.x + 0.4, y: 5.05, w: 5.0, h: 0.5, fontSize: 14.5, bold: true, italic: true, color: c.col, fontFace: "Arial" });
  });
  s.addText("Dense alone is fooled by paraphrase; lexical alone is fooled by stuffing. Fusing both — then gating on role coherence — beats either.", {
    x: 0.7, y: 6.05, w: 12, h: 0.5, fontSize: 15, italic: true, color: MUTED, fontFace: "Arial" });
  pageNum(s, 4);

  // ============================================================= 5 ARCHITECTURE
  s = p.addSlide();
  s.background = { color: WHITE };
  s.addText("How it works", { x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria" });
  s.addText("Five explainable base components, two multipliers, one kill-switch — all CPU, deterministic, defensible line by line.", {
    x: 0.72, y: 1.25, w: 11.8, h: 0.5, fontSize: 16, color: MUTED, fontFace: "Arial" });

  const comps = [
    { i: ic.search, t: "Role coherence  (0.30)", d: "Non-technical title penalized hard — the anti-trap gate." },
    { i: ic.brain, t: "Build evidence  (0.22)", d: "Ranking / search / rec work mined from career descriptions." },
    { i: ic.layers, t: "Hybrid semantics  (0.20)", d: "TF-IDF fused with bge-small dense embeddings of the narrative." },
    { i: ic.map, t: "Location fit  (0.18)", d: "India required; Pune/Noida preferred; abroad down-weighted." },
    { i: ic.chart, t: "Experience band  (0.10)", d: "Soft curve peaking at the JD's 6–8 year ideal." },
  ];
  comps.forEach((c, idx) => {
    const col = idx % 3, row = Math.floor(idx / 3);
    const x = 0.7 + col * 4.05, y = 2.05 + row * 1.7;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w: 3.75, h: 1.5, fill: { color: CARD }, rectRadius: 0.1, shadow: shadow() });
    s.addImage({ data: c.i, x: x + 0.25, y: y + 0.28, w: 0.5, h: 0.5 });
    s.addText(c.t, { x: x + 0.9, y: y + 0.18, w: 2.7, h: 0.45, fontSize: 14.5, bold: true, color: INK, fontFace: "Arial", valign: "middle" });
    s.addText(c.d, { x: x + 0.9, y: y + 0.62, w: 2.75, h: 0.8, fontSize: 11.5, color: "475569", fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.0 });
  });
  // multipliers + honeypot card in the 6th cell
  const x6 = 0.7 + 2 * 4.05, y6 = 2.05 + 1.7;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: x6, y: y6, w: 3.75, h: 1.5, fill: { color: NAVY }, rectRadius: 0.1, shadow: shadow() });
  s.addImage({ data: ic.shield, x: x6 + 0.25, y: y6 + 0.28, w: 0.5, h: 0.5 });
  s.addText("Modifiers", { x: x6 + 0.9, y: y6 + 0.18, w: 2.7, h: 0.45, fontSize: 14.5, bold: true, color: TEAL_L, fontFace: "Arial", valign: "middle" });
  s.addText("× disqualifiers  · × availability  · honeypot → bottom", { x: x6 + 0.9, y: y6 + 0.62, w: 2.75, h: 0.8, fontSize: 11.5, color: "CADCFC", fontFace: "Arial", valign: "top" });

  s.addText([
    { text: "score", options: { italic: true, color: MUTED } },
    { text: "  =  (Σ weighted components)  ×  disqualifier-penalty  ×  behavioral-availability,   honeypots forced to 0", options: { color: INK } },
  ], { x: 0.7, y: 5.7, w: 12, h: 0.5, fontSize: 14.5, fontFace: "Courier New", align: "left" });
  s.addText("Reasoning is assembled deterministically from real fields — specific, non-hallucinated, rank-consistent (what Stage-4 review rewards).", {
    x: 0.7, y: 6.35, w: 12, h: 0.5, fontSize: 13.5, italic: true, color: MUTED, fontFace: "Arial" });
  pageNum(s, 5);

  // ============================================================= 6 PIPELINE / USAGE
  s = p.addSlide();
  s.background = { color: WHITE };
  s.addText("From candidates.jsonl to a shortlist a recruiter trusts", {
    x: 0.7, y: 0.5, w: 12.2, h: 0.7, fontSize: 28, bold: true, color: INK, fontFace: "Cambria" });

  const steps = [
    { i: ic.gear, t: "1 · Precompute (offline)", d: "Embed 100K career narratives with bge-small. No time limit — not the ranking step." },
    { i: ic.bolt, t: "2 · Rank (CPU, offline)", d: "Hybrid score + gates + multipliers. 55s wall-clock, no network, < 16 GB." },
    { i: ic.file, t: "3 · Output", d: "Validated top-100 CSV with a plain-language reason per candidate." },
    { i: ic.code, t: "4 · Verify", d: "Local eval + guardrails; one-command repro; Streamlit sandbox demo." },
  ];
  steps.forEach((c, i) => {
    const x = 0.7 + i * 3.08;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 1.7, w: 2.85, h: 2.9, fill: { color: CARD }, rectRadius: 0.12, shadow: shadow() });
    s.addImage({ data: c.i, x: x + 0.3, y: 2.0, w: 0.55, h: 0.55 });
    s.addText(c.t, { x: x + 0.25, y: 2.7, w: 2.4, h: 0.6, fontSize: 14.5, bold: true, color: INK, fontFace: "Arial" });
    s.addText(c.d, { x: x + 0.25, y: 3.3, w: 2.45, h: 1.2, fontSize: 12, color: "475569", fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.05 });
    if (i < 3) s.addText("→", { x: x + 2.78, y: 2.7, w: 0.35, h: 0.6, fontSize: 22, bold: true, color: TEAL, align: "center", valign: "middle" });
  });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 4.95, w: 11.95, h: 1.5, fill: { color: NAVY }, rectRadius: 0.1, shadow: shadow() });
  s.addText("Reproduce in one command", { x: 1.0, y: 5.15, w: 11, h: 0.4, fontSize: 13, bold: true, color: TEAL_L, fontFace: "Arial" });
  s.addText("python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv", {
    x: 1.0, y: 5.55, w: 11.3, h: 0.5, fontSize: 15, color: WHITE, fontFace: "Courier New" });
  s.addText("Meets every compute constraint: CPU-only · network off · ≤ 16 GB RAM · well under the 5-minute budget.", {
    x: 0.7, y: 6.7, w: 12, h: 0.4, fontSize: 13.5, italic: true, color: MUTED, fontFace: "Arial" });
  pageNum(s, 6);

  // ============================================================= 7 RESULTS
  s = p.addSlide();
  s.background = { color: WHITE };
  s.addText("Results on the real pool", {
    x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria" });
  s.addText("Versus the organizers' own sample ranking — which put HR Managers and Accountants at the top — this system avoids the trap entirely.", {
    x: 0.72, y: 1.25, w: 11.9, h: 0.5, fontSize: 15.5, color: MUTED, fontFace: "Arial" });

  const res = [
    { n: "0", l: "honeypots in top 100", c: TEAL },
    { n: "0", l: "non-technical roles in top 100", c: TEAL },
    { n: "10/10", l: "top-10 are India AI/ML engineers", c: TEAL },
    { n: "55s", l: "runtime  (budget 300s)", c: TEAL },
  ];
  res.forEach((r, i) => {
    const x = 0.7 + i * 3.05;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 1.95, w: 2.8, h: 1.55, fill: { color: CARDTEAL }, rectRadius: 0.12, shadow: shadow() });
    s.addText(r.n, { x: x + 0.1, y: 2.1, w: 2.6, h: 0.8, fontSize: 34, bold: true, color: r.c, fontFace: "Cambria", align: "center", valign: "middle" });
    s.addText(r.l, { x: x + 0.15, y: 2.9, w: 2.5, h: 0.55, fontSize: 11.5, color: "475569", fontFace: "Arial", align: "center", valign: "top" });
  });

  s.addText("Who the shortlist actually surfaces (top-100 role families)", {
    x: 0.7, y: 3.75, w: 8, h: 0.4, fontSize: 14, bold: true, color: INK, fontFace: "Arial" });
  s.addChart(p.charts.BAR, [{
    name: "count",
    labels: ["Recommendation Sys Eng", "Applied ML Engineer", "AI Engineer", "Senior Data Scientist", "NLP / Search Engineer"],
    values: [16, 12, 10, 9, 15]
  }], {
    x: 0.6, y: 4.1, w: 7.4, h: 2.9, barDir: "bar",
    chartColors: [TEAL], showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK,
    catAxisLabelColor: "475569", catAxisLabelFontSize: 11,
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, valAxisMaxVal: 20,
  });

  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 8.3, y: 4.1, w: 4.4, h: 2.9, fill: { color: CARD }, rectRadius: 0.12, shadow: shadow() });
  s.addText("Sample reasoning (rank 1)", { x: 8.55, y: 4.3, w: 4.0, h: 0.4, fontSize: 13, bold: true, color: TEAL, fontFace: "Arial" });
  s.addText("\u201CSenior Machine Learning Engineer with 7.2 yrs; career shows re-ranking; Pune/Noida-based; responsive to recruiters (61%).\u201D", {
    x: 8.55, y: 4.75, w: 3.95, h: 1.4, fontSize: 13, italic: true, color: INK, fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.15 });
  s.addText("Specific · grounded in real fields · matches the rank.", { x: 8.55, y: 6.3, w: 3.95, h: 0.5, fontSize: 11.5, color: MUTED, fontFace: "Arial" });
  pageNum(s, 7);

  // ============================================================= 8 WHY IT WINS (dark close)
  s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("Built to survive every stage", {
    x: 0.7, y: 0.7, w: 12, h: 0.8, fontSize: 34, bold: true, color: WHITE, fontFace: "Cambria" });
  s.addText("The composite weights NDCG@10 at 50% — so the system is engineered to be ruthless and precise at the very top.", {
    x: 0.72, y: 1.55, w: 11.8, h: 0.5, fontSize: 16, color: "CADCFC", fontFace: "Arial" });

  const wins = [
    { i: ic.check, t: "Stage 3 — reproduction", d: "One command, CPU-only, no network, 55s. Honeypot rate 0%." },
    { i: ic.check, t: "Stage 4 — review", d: "Modular, documented code; specific non-hallucinated reasoning; real git iteration." },
    { i: ic.check, t: "Stage 5 — defense", d: "Every weight and gate is hand-encoded from the JD and explainable in plain terms." },
  ];
  wins.forEach((c, i) => {
    const x = 0.7 + i * 4.05;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.5, w: 3.75, h: 2.7, fill: { color: NAVY2 }, rectRadius: 0.12, shadow: shadow() });
    s.addImage({ data: c.i, x: x + 0.32, y: 2.85, w: 0.55, h: 0.55 });
    s.addText(c.t, { x: x + 0.32, y: 3.55, w: 3.1, h: 0.5, fontSize: 17, bold: true, color: WHITE, fontFace: "Arial" });
    s.addText(c.d, { x: x + 0.32, y: 4.1, w: 3.15, h: 1.0, fontSize: 13, color: "9FB3C8", fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.1 });
  });
  s.addText([
    { text: "Not an AI-keyword counter. ", options: { bold: true, color: TEAL_L } },
    { text: "A system that reads profiles the way a great recruiter does.", options: { color: WHITE } },
  ], { x: 0.7, y: 5.7, w: 12, h: 0.6, fontSize: 19, fontFace: "Cambria", align: "center" });

  await p.writeFile({ fileName: "/home/claude/redrob-ranker/deck/Redrob_Ranker_Deck.pptx" });
  console.log("deck written");
})();
