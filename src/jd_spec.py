"""
jd_spec.py
==========
Structured encoding of the released Job Description (Senior AI Engineer,
Founding Team @ Redrob AI).

Design philosophy
-----------------
The JD is not a keyword checklist. It explicitly states that ranking by
"most AI keywords in the skills section" is a trap baked into the dataset.
So this module encodes what the JD *means*, not just what it says:

  * the genuine must-have capabilities (retrieval / ranking / search / rec
    systems shipped to real users at product companies),
  * the explicit disqualifiers the company says it actually applies,
  * the behavioural reality that an unavailable candidate is not a hire.

These structures are consumed by the feature extractor and the scorer.
Everything here is hand-encoded from the JD text so it can be defended,
line by line, at the Stage-5 interview.
"""

# ---------------------------------------------------------------------------
# Retrieval query (used for both TF-IDF and dense semantic matching).
# Phrased the way an *ideal* candidate's career narrative would read, so that
# semantic similarity rewards people who DID the work even if they never use
# the buzzwords.
# ---------------------------------------------------------------------------
JD_QUERY = (
    "Senior AI engineer who has shipped end-to-end ranking, search, retrieval "
    "and recommendation systems to real users at scale at a product company. "
    "Production experience with embeddings-based retrieval (sentence transformers, "
    "BGE, E5, OpenAI embeddings), vector databases and hybrid search "
    "(FAISS, Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch). "
    "Strong Python engineering and code quality. Designs evaluation frameworks "
    "for ranking systems using NDCG, MRR, MAP, offline-to-online correlation and "
    "A/B testing. Applied machine learning in production, not pure research. "
    "Scrappy product-engineering attitude, ships fast, owns the intelligence layer."
)

# ---------------------------------------------------------------------------
# Title taxonomy. The single most decisive anti-trap signal: a Marketing
# Manager with 9 AI skills is NOT a fit, no matter how perfect the skills list.
# Matching is done on lowercased substring of title.
# ---------------------------------------------------------------------------
CORE_AI_TITLES = [
    "ai engineer", "ml engineer", "machine learning engineer", "machine learning",
    "applied scientist", "applied ml", "research engineer", "ml scientist",
    "nlp engineer", "nlp scientist", "search engineer", "ranking engineer",
    "recommendation", "recommender", "relevance engineer", "data scientist",
    "mlops", "ml platform", "ai scientist", "deep learning",
]

ADJACENT_TECH_TITLES = [
    "software engineer", "software developer", "backend engineer", "back end",
    "full stack", "fullstack", "data engineer", "devops", "cloud engineer",
    "platform engineer", "sde", "python developer", "java developer",
    ".net developer", "frontend", "front end", "mobile developer",
    "systems engineer", "infrastructure engineer", "staff engineer",
    "principal engineer", "engineering manager", "tech lead", "architect",
]

# The trap bucket. ~70% of the pool sits here. Strong penalty regardless of skills.
NON_TECH_TITLES = [
    "hr manager", "human resources", "recruiter", "talent acquisition",
    "accountant", "accounts", "finance manager", "marketing manager", "marketing",
    "sales executive", "sales manager", "business development",
    "content writer", "copywriter", "graphic designer", "ux designer", "ui designer",
    "customer support", "customer success", "operations manager", "operations",
    "business analyst", "project manager", "program manager", "product manager",
    "civil engineer", "mechanical engineer", "electrical engineer", "chemical engineer",
    "teacher", "consultant", "administrator", "executive assistant",
]

# ---------------------------------------------------------------------------
# Evidence of genuinely having built the systems the JD cares about.
# Searched inside career-history *descriptions* (what they did), never the
# skills list (what they claimed).
# ---------------------------------------------------------------------------
BUILD_EVIDENCE_TERMS = [
    "recommendation system", "recommender", "recsys", "ranking", "learning to rank",
    "search relevance", "semantic search", "information retrieval", "retrieval",
    "embedding", "embeddings", "vector search", "vector database", "faiss",
    "elasticsearch", "opensearch", "pinecone", "weaviate", "qdrant", "milvus",
    "bm25", "personalization", "personalisation", "relevance", "ndcg", "mrr",
    "matching engine", "candidate generation", "nearest neighbor", "ann index",
    "click-through", "ctr prediction", "a/b test", "ab test", "offline evaluation",
    "feature store", "two-tower", "re-ranking", "reranking",
]

# Strong, high-value evidence (counts double).
BUILD_EVIDENCE_STRONG = [
    "recommendation system", "recommender", "recsys", "learning to rank",
    "search relevance", "semantic search", "information retrieval",
    "vector search", "re-ranking", "reranking", "candidate generation", "two-tower",
]

PRODUCTION_TERMS = [
    "production", "deployed", "real users", "at scale", "shipped", "launched",
    "serving", "latency", "throughput", "live traffic", "real-time", "real time",
]

# ---------------------------------------------------------------------------
# Disqualifiers the company says it actually applies.
# ---------------------------------------------------------------------------
SERVICES_COMPANIES = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "tech mahindra", "hcl", "mindtree", "ltimindtree", "l&t infotech",
    "mphasis", "dxc", "hexaware", "igate", "syntel", "birlasoft", "zensar",
]

# Computer-vision / speech / robotics primary without NLP/IR -> not a fit.
CV_SPEECH_ROBOTICS_TERMS = [
    "computer vision", "image classification", "object detection", "segmentation",
    "opencv", "facial recognition", "ocr", "speech recognition", "asr",
    "text to speech", "tts", "audio", "robotics", "slam", "lidar", "autonomous vehicle",
    "point cloud",
]
NLP_IR_TERMS = [
    "nlp", "natural language", "language model", "llm", "text", "bert", "transformer",
    "retrieval", "search", "ranking", "recommendation", "embedding", "information retrieval",
    "question answering", "summarization", "entity",
]

RESEARCH_ONLY_TERMS = [
    "phd researcher", "postdoc", "research fellow", "research associate",
    "research scientist", "academic", "university", "laboratory", "lab",
    "published", "publications",
]

# ---------------------------------------------------------------------------
# Location. Pune/Noida preferred; named Tier-1 Indian cities welcome;
# outside India: case-by-case, NO visa sponsorship -> heavy down-weight.
# ---------------------------------------------------------------------------
PREFERRED_CITIES = ["pune", "noida"]
TIER1_INDIA_CITIES = [
    "mumbai", "bangalore", "bengaluru", "hyderabad", "delhi", "new delhi",
    "gurgaon", "gurugram", "ncr", "chennai", "kolkata", "ahmedabad",
]

# ---------------------------------------------------------------------------
# Scoring weights for the base fit score (sum = 1.0). Tunable; documented so
# the choices can be defended. Title coherence and real build-evidence are the
# heaviest because they are what separates true fits from keyword stuffers.
# ---------------------------------------------------------------------------
WEIGHTS = {
    "domain":     0.26,   # title / role coherence  (anti-trap gate)
    "evidence":   0.20,   # genuine ranking/search/rec build evidence
    "semantic":   0.18,   # hybrid TF-IDF + dense similarity to JD
    "location":   0.16,   # India / Pune-Noida requirement (hard constraint in JD)
    "credibility":0.12,   # skill-trust, assessments, activity (anti-stuffing)
    "experience": 0.08,   # soft band around 6-8 yrs
}

# Experience band from the JD ("ideal" 6-8, range 5-9, soft outside).
EXP_IDEAL_LOW, EXP_IDEAL_HIGH = 6.0, 8.0
EXP_BAND_LOW, EXP_BAND_HIGH = 5.0, 9.0
