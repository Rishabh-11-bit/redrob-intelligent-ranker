const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

const NAVY = "0F2A3F", NAVY2 = "163b54", TEAL = "0D9488", TEAL_L = "2DD4BF";
const INK = "1E293B", MUTED = "64748B", CARD = "F1F5F9", CARDTEAL = "ECFDF8", WHITE = "FFFFFF";

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color, size: String(size) }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}
const sh = () => ({ type: "outer", color: "000000", blur: 7, offset: 3, angle: 90, opacity: 0.12 });

(async () => {
  const p = new pptxgen();
  p.layout = "LAYOUT_WIDE"; p.author = "Rishabh Gaikwad"; p.title = "Redrob Fit — Ideathon Challenge 1";
  const W = 13.3;
  const ic = {
    bolt: await icon(FA.FaBolt, "#" + TEAL_L), brain: await icon(FA.FaBrain, "#" + TEAL),
    search: await icon(FA.FaSearch, "#" + TEAL), shield: await icon(FA.FaShieldAlt, "#" + TEAL),
    user: await icon(FA.FaUserCheck, "#" + TEAL), file: await icon(FA.FaFileAlt, "#" + TEAL),
    list: await icon(FA.FaListOl, "#" + TEAL), bulb: await icon(FA.FaLightbulb, "#" + TEAL_L),
    star: await icon(FA.FaStar, "#" + TEAL_L),
  };
  const pageNum = (s, n) => s.addText(`${n}`, { x: W - 0.7, y: 7.0, w: 0.4, h: 0.3, fontSize: 10, color: MUTED, align: "right", fontFace: "Arial" });

  // 1 TITLE
  let s = p.addSlide(); s.background = { color: NAVY };
  s.addImage({ data: ic.bolt, x: 0.7, y: 0.85, w: 0.6, h: 0.6 });
  s.addText("IDEATHON · CHALLENGE 1 — BUILD AN AI SYSTEM", { x: 1.45, y: 0.9, w: 11, h: 0.5, fontSize: 15, color: TEAL_L, bold: true, charSpacing: 2, fontFace: "Arial", valign: "middle" });
  s.addText("Redrob Fit", { x: 0.7, y: 2.2, w: 11.9, h: 1.1, fontSize: 54, bold: true, color: WHITE, fontFace: "Cambria" });
  s.addText("A recruiter copilot that ranks candidates for fit — not keywords", { x: 0.72, y: 3.4, w: 11.5, h: 0.7, fontSize: 22, color: "CADCFC", fontFace: "Arial" });
  s.addText("Paste a job description. Get a trustworthy, reasoned shortlist from a 100K pool in under a minute — on a laptop, no cloud.", { x: 0.72, y: 4.3, w: 11.3, h: 0.7, fontSize: 15, color: "9FB3C8", fontFace: "Arial" });
  s.addText("Rishabh Gaikwad", { x: 0.72, y: 6.4, w: 11, h: 0.4, fontSize: 14, bold: true, color: WHITE, fontFace: "Arial" });

  // 2 CHALLENGE + PROBLEM
  s = p.addSlide(); s.background = { color: WHITE };
  s.addText("The challenge — and why it matters", { x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria" });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 1.5, w: 12, h: 1.0, fill: { color: CARDTEAL }, rectRadius: 0.1, shadow: sh() });
  s.addImage({ data: ic.bulb ? await icon(FA.FaLightbulb, "#" + TEAL) : ic.bulb, x: 1.0, y: 1.72, w: 0.55, h: 0.55 });
  s.addText([
    { text: "Challenge 1 — Build an AI System. ", options: { bold: true, color: TEAL } },
    { text: "An AI-native system that makes real work smarter: intelligent search + ranking that changes how recruiters hire.", options: { color: INK } },
  ], { x: 1.75, y: 1.5, w: 10.7, h: 1.0, fontSize: 16, fontFace: "Arial", valign: "middle" });

  const cards = [
    { t: "Recruiters drown", d: "Hundreds of profiles per role. Keyword filters surface whoever stuffed the most buzzwords — and bury the genuinely qualified." },
    { t: "Keywords ≠ fit", d: "An HR Manager listing 9 AI skills out-ranks an engineer who actually shipped a recommender but never wrote \u201CRAG.\u201D" },
    { t: "Availability ignored", d: "A perfect resume that's been inactive for months is a dead end recruiters only discover after wasting outreach." },
  ];
  cards.forEach((c, i) => {
    const x = 0.7 + i * 4.05;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.9, w: 3.75, h: 3.2, fill: { color: CARD }, rectRadius: 0.12, shadow: sh() });
    s.addText(c.t, { x: x + 0.32, y: 3.2, w: 3.1, h: 0.5, fontSize: 18, bold: true, color: INK, fontFace: "Arial" });
    s.addText(c.d, { x: x + 0.32, y: 3.8, w: 3.15, h: 2.1, fontSize: 14, color: "475569", fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.1 });
  });
  s.addText("Hiring is a ranking problem dressed up as a search box. We fix the ranking.", { x: 0.7, y: 6.35, w: 12, h: 0.5, fontSize: 15, italic: true, color: MUTED, fontFace: "Arial" });
  pageNum(s, 2);

  // 3 SOLUTION
  s = p.addSlide(); s.background = { color: WHITE };
  s.addText("The solution — how Redrob Fit works", { x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria" });
  s.addText("It reads the JD's intent, then judges each candidate the way a great recruiter would — and shows its reasoning.", { x: 0.72, y: 1.25, w: 11.8, h: 0.5, fontSize: 16, color: MUTED, fontFace: "Arial" });

  const steps = [
    { i: ic.brain, t: "Understands the role", d: "Parses the JD into real requirements, must-haves and disqualifiers — not a keyword bag." },
    { i: ic.search, t: "Judges the whole person", d: "Hybrid semantic + lexical match on what they DID, plus career trajectory and platform signals." },
    { i: ic.shield, t: "Filters noise & traps", d: "Down-weights keyword-stuffers and the unavailable; detects impossible profiles." },
    { i: ic.file, t: "Explains every pick", d: "A plain-language reason per candidate, so a recruiter can trust and act on the list." },
  ];
  steps.forEach((c, i) => {
    const x = 0.7 + i * 3.08;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.0, w: 2.85, h: 3.0, fill: { color: CARD }, rectRadius: 0.12, shadow: sh() });
    s.addImage({ data: c.i, x: x + 0.3, y: 2.3, w: 0.55, h: 0.55 });
    s.addText(c.t, { x: x + 0.25, y: 3.0, w: 2.4, h: 0.7, fontSize: 15, bold: true, color: INK, fontFace: "Arial" });
    s.addText(c.d, { x: x + 0.25, y: 3.65, w: 2.45, h: 1.3, fontSize: 12, color: "475569", fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.1 });
  });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 5.35, w: 12, h: 1.15, fill: { color: NAVY }, rectRadius: 0.1, shadow: sh() });
  s.addText([
    { text: "Runs on a laptop. ", options: { bold: true, color: TEAL_L } },
    { text: "100K candidates ranked in under a minute, fully offline — no per-candidate LLM calls, so it scales to millions in production.", options: { color: WHITE } },
  ], { x: 1.0, y: 5.35, w: 11.4, h: 1.15, fontSize: 16, fontFace: "Arial", valign: "middle" });
  pageNum(s, 3);

  // 4 USER JOURNEY
  s = p.addSlide(); s.background = { color: WHITE };
  s.addText("The user journey", { x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria" });
  s.addText("Priya, a startup recruiter, needs one founding AI engineer from a 100K pool.", { x: 0.72, y: 1.25, w: 11.8, h: 0.5, fontSize: 16, color: MUTED, fontFace: "Arial" });

  const journey = [
    { n: "1", t: "Paste the JD", d: "Priya drops the full job description in — messy prose, disqualifiers and all." },
    { n: "2", t: "System reads intent", d: "Redrob Fit extracts what the role truly needs and what to avoid." },
    { n: "3", t: "Ranks the pool", d: "Every candidate scored on fit, evidence, location and availability." },
    { n: "4", t: "Reasoned shortlist", d: "Top matches appear with a one-line why and an honest concern each." },
    { n: "5", t: "Priya acts", d: "She reaches out to 10 real fits instead of sifting 1,000 maybes." },
  ];
  journey.forEach((c, i) => {
    const x = 0.7 + i * 2.43;
    s.addShape(p.shapes.OVAL, { x: x + 0.85, y: 2.1, w: 0.7, h: 0.7, fill: { color: TEAL }, shadow: sh() });
    s.addText(c.n, { x: x + 0.85, y: 2.1, w: 0.7, h: 0.7, fontSize: 22, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: "Arial" });
    s.addText(c.t, { x: x + 0.05, y: 3.0, w: 2.3, h: 0.5, fontSize: 14.5, bold: true, color: INK, align: "center", fontFace: "Arial" });
    s.addText(c.d, { x: x + 0.05, y: 3.5, w: 2.3, h: 1.5, fontSize: 12, color: "475569", align: "center", fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.1 });
    if (i < 4) s.addText("\u2192", { x: x + 2.18, y: 2.1, w: 0.5, h: 0.7, fontSize: 24, bold: true, color: TEAL, align: "center", valign: "middle" });
  });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 5.4, w: 12, h: 1.0, fill: { color: CARDTEAL }, rectRadius: 0.1, shadow: sh() });
  s.addText([
    { text: "Time to a trustworthy shortlist: ", options: { color: INK } },
    { text: "days \u2192 under a minute.", options: { bold: true, color: TEAL } },
  ], { x: 1.0, y: 5.4, w: 11.4, h: 1.0, fontSize: 17, fontFace: "Arial", valign: "middle" });
  pageNum(s, 4);

  // 5 WIREFRAME / MOCKUP
  s = p.addSlide(); s.background = { color: WHITE };
  s.addText("Wireframe — the recruiter view", { x: 0.7, y: 0.5, w: 12, h: 0.7, fontSize: 32, bold: true, color: INK, fontFace: "Cambria" });

  // left: JD input panel
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 1.5, w: 4.1, h: 5.0, fill: { color: CARD }, rectRadius: 0.1, shadow: sh() });
  s.addText("Job description", { x: 0.95, y: 1.7, w: 3.6, h: 0.4, fontSize: 14, bold: true, color: INK, fontFace: "Arial" });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.95, y: 2.15, w: 3.6, h: 3.4, fill: { color: WHITE }, rectRadius: 0.06, line: { color: "CBD5E1", width: 1 } });
  s.addText("Senior AI Engineer, founding team. Must have shipped ranking / retrieval to real users at a product company. Pune/Noida. No pure-research, no keyword stuffers\u2026", { x: 1.12, y: 2.32, w: 3.3, h: 3.1, fontSize: 11.5, color: "475569", fontFace: "Arial", valign: "top", lineSpacingMultiple: 1.15 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.95, y: 5.7, w: 3.6, h: 0.6, fill: { color: TEAL }, rectRadius: 0.08, shadow: sh() });
  s.addText("Rank candidates", { x: 0.95, y: 5.7, w: 3.6, h: 0.6, fontSize: 14, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: "Arial" });

  // right: ranked shortlist cards
  s.addText("Ranked shortlist", { x: 5.1, y: 1.55, w: 7.5, h: 0.4, fontSize: 14, bold: true, color: INK, fontFace: "Arial" });
  const picks = [
    { r: "1", n: "ML Engineer · 7.2 yrs · Noida", why: "Built re-ranking at a product co · open to work · 61% response", sc: "0.99" },
    { r: "2", n: "Recommendation Sys Eng · 6.1 yrs · Pune", why: "Shipped recommender + semantic search · responsive", sc: "0.98" },
    { r: "3", n: "Applied ML Engineer · 6.2 yrs · Ahmedabad", why: "Retrieval + relevance work · concern: notice period", sc: "0.97" },
  ];
  picks.forEach((c, i) => {
    const y = 2.05 + i * 1.4;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 5.1, y, w: 7.5, h: 1.2, fill: { color: i === 0 ? CARDTEAL : CARD }, rectRadius: 0.1, shadow: sh() });
    s.addShape(p.shapes.OVAL, { x: 5.35, y: y + 0.32, w: 0.55, h: 0.55, fill: { color: TEAL } });
    s.addText(c.r, { x: 5.35, y: y + 0.32, w: 0.55, h: 0.55, fontSize: 18, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: "Arial" });
    s.addText(c.n, { x: 6.1, y: y + 0.18, w: 5.2, h: 0.4, fontSize: 14, bold: true, color: INK, fontFace: "Arial" });
    s.addImage({ data: ic.user, x: 6.1, y: y + 0.62, w: 0.28, h: 0.28 });
    s.addText(c.why, { x: 6.45, y: y + 0.6, w: 4.9, h: 0.5, fontSize: 11.5, color: "475569", fontFace: "Arial", valign: "middle" });
    s.addText(c.sc, { x: 11.4, y: y + 0.2, w: 1.0, h: 0.5, fontSize: 18, bold: true, color: TEAL, align: "right", fontFace: "Cambria" });
  });
  s.addText("Every row carries a reason and an honest concern — the recruiter trusts the list because it shows its work.", { x: 5.1, y: 6.35, w: 7.5, h: 0.5, fontSize: 12.5, italic: true, color: MUTED, fontFace: "Arial" });
  pageNum(s, 5);

  await p.writeFile({ fileName: "/home/claude/redrob-ranker/deck/Ideathon_Challenge1_Deck.pptx" });
  console.log("ideathon deck written");
})();
