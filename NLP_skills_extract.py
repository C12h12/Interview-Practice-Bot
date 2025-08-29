# ---------- utils_skills.py (you can paste into your streamlit file too) ----------
import re
import fitz  # PyMuPDF
import docx2txt
import spacy
from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer, util

# 1) Read text from uploaded files
import fitz  # PyMuPDF
import docx2txt

def read_file(file):
    name = file.name.lower()

    if name.endswith(".txt"):
        file.seek(0)  # reset pointer
        return file.read().decode("utf-8", errors="ignore")

    elif name.endswith(".docx"):
        file.seek(0)  # reset pointer
        return docx2txt.process(file)

    elif name.endswith(".pdf"):
        file.seek(0)  # reset pointer
        text = ""
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        for page in pdf:
            text += page.get_text("text")
        return text

    else:
        return ""


# 2) Load NLP + embedder once (cache in Streamlit outside if you want)
def load_nlp_and_embedder():
    nlp = spacy.load("en_core_web_sm")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return nlp, embedder

# 3) Build/Load your skills catalog (extend with ESCO/O*NET later)
BASE_SKILLS = [
    # --- technical ---
    "Python", "Java", "C++", "C", "Go", "JavaScript", "TypeScript", "React",
    "Node.js", "Django", "Flask", "FastAPI", "Spring Boot",
    "SQL", "NoSQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "Data Structures", "Algorithms", "Object-Oriented Programming",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "Pandas", "NumPy", "TensorFlow", "PyTorch", "Scikit-learn",
    "MLOps", "CI/CD", "Docker", "Kubernetes", "Git", "Linux",
    "Cloud Computing", "AWS", "Azure", "GCP",
    "REST APIs", "GraphQL", "Microservices",
    # --- soft / general ---
    "Communication", "Teamwork", "Leadership", "Problem Solving",
    "Time Management", "Adaptability", "Critical Thinking",
    # --- data/analytics ---
    "Data Analysis", "Data Visualization", "Power BI", "Tableau", "Excel",
]

def normalize(s: str) -> str:
    s = re.sub(r"[\(\)\[\]\{\}\.,/\\\-_\+]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# 4) Candidate generation with spaCy (noun chunks + ents + frequent n-grams)
def generate_candidates(text: str, nlp):
    text_clean = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove weird unicode
    doc = nlp(text_clean)

    # noun chunks + named entities + fine POS patterns
    cand = set()
    for chunk in doc.noun_chunks:
        c = normalize(chunk.text)
        if 2 <= len(c) <= 50:
            cand.add(c)

    for ent in doc.ents:
        c = normalize(ent.text)
        if 2 <= len(c) <= 50:
            cand.add(c)

    # Add uni/bi/tri-grams from tokens (good for short skills like "Git")
    toks = [t.text for t in doc if not t.is_space]
    for n in (1, 2, 3):
        for i in range(len(toks) - n + 1):
            phrase = normalize(" ".join(toks[i : i + n]))
            if 2 <= len(phrase) <= 50:
                cand.add(phrase)

    # Heuristic filter: drop very generic words
    bad = {"experience", "project", "projects", "knowledge", "skills", "framework", "tools", "technology", "technologies", "years"}
    candidates = {c for c in cand if c.lower() not in bad}
    return candidates

# 5) Smart matching: exact → fuzzy → semantic
def smart_match_skills(candidates, catalog, embedder, fuzzy_cutoff=90, semantic_threshold=0.72):
    # Fast exact case-insensitive map
    cat_norm_map = {normalize(s).lower(): s for s in catalog}
    cat_norm_list = list(cat_norm_map.keys())

    matched = set()

    # Pre-embed catalog for semantic step
    cat_embeddings = embedder.encode(cat_norm_list, convert_to_tensor=True, normalize_embeddings=True)

    for cand in candidates:
        c_norm = normalize(cand).lower()
        # exact
        if c_norm in cat_norm_map:
            matched.add(cat_norm_map[c_norm])
            continue

        # fuzzy (top-3 suggestions)
        fuzzy_hits = process.extract(c_norm, cat_norm_list, scorer=fuzz.WRatio, limit=3)
        high = [k for k, score, _ in fuzzy_hits if score >= fuzzy_cutoff]
        if high:
            for k in high:
                matched.add(cat_norm_map[k])
            continue

        # semantic: compare candidate to catalog with embeddings
        c_emb = embedder.encode(c_norm, convert_to_tensor=True, normalize_embeddings=True)
        cos = util.cos_sim(c_emb, cat_embeddings)[0]
        top_idx = int(cos.argmax())
        top_sim = float(cos[top_idx])
        if top_sim >= semantic_threshold:
            matched.add(cat_norm_map[cat_norm_list[top_idx]])

    return matched

# 6) One-call extractor
def extract_skills_smart(text, catalog=None, nlp=None, embedder=None,
                         fuzzy_cutoff=90, semantic_threshold=0.72):
    if catalog is None:
        catalog = BASE_SKILLS
    if nlp is None or embedder is None:
        nlp, embedder = load_nlp_and_embedder()

    cands = generate_candidates(text, nlp)
    return smart_match_skills(cands, catalog, embedder,
                              fuzzy_cutoff=fuzzy_cutoff,
                              semantic_threshold=semantic_threshold)
