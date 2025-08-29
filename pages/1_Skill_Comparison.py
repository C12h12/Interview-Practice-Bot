import streamlit as st
import matplotlib.pyplot as plt
from NLP_skills_extract import read_file, extract_skills_smart, BASE_SKILLS

# HuggingFace Zero-Shot Classification
from transformers import pipeline

st.title("Skill Comparison (Zero-Shot Categorization)")

# ---------------- Caching ----------------
@st.cache_resource
def load_zero_shot_classifier():
    """Load HuggingFace zero-shot classifier only once."""
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

classifier = load_zero_shot_classifier()

candidate_labels = ["HR", "Technical"]

@st.cache_data
def categorize_skills(skills):
    """Categorize a set of skills into HR or Technical using zero-shot classification."""
    hr_set, tech_set = set(), set()
    for skill in skills:
        result = classifier(skill, candidate_labels=candidate_labels)
        top_label = result["labels"][0]
        if top_label == "HR":
            hr_set.add(skill)
        else:
            tech_set.add(skill)
    return hr_set, tech_set

# ---------------- Main Logic ----------------
if not st.session_state.get("jd_file") or not st.session_state.get("resume_file"):
    st.warning("⚠️ Please upload files in **Home** first.")
else:
    # Read text from uploaded files (cached in utils_skills.py)
    jd_text = read_file(st.session_state.jd_file)
    resume_text = read_file(st.session_state.resume_file)

    # Extract skills (cached in utils_skills.py)
    jd_skills = extract_skills_smart(jd_text, BASE_SKILLS)
    resume_skills = extract_skills_smart(resume_text, BASE_SKILLS)

    missing_skills = jd_skills - resume_skills
    present_skills = jd_skills & resume_skills

    # Categorize present and missing skills
    present_hr, present_tech = categorize_skills(present_skills)
    missing_hr, missing_tech = categorize_skills(missing_skills)

    # Save results to session_state
    st.session_state.present_hr = present_hr
    st.session_state.present_tech = present_tech
    st.session_state.missing_hr = missing_hr
    st.session_state.missing_tech = missing_tech

    # ---------------- Display Results ----------------
    st.subheader("✅ Skills found in Resume")
    st.write("**HR Skills:**", ", ".join(present_hr) if present_hr else "None")
    st.write("**Technical Skills:**", ", ".join(present_tech) if present_tech else "None")

    st.subheader("❌ Skills missing from Resume")
    st.write("**HR Skills:**", ", ".join(missing_hr) if missing_hr else "None")
    st.write("**Technical Skills:**", ", ".join(missing_tech) if missing_tech else "None")

    # ---------------- Visualization ----------------
    fig, ax = plt.subplots()
    categories = ["HR Present", "HR Missing", "Tech Present", "Tech Missing"]
    values = [len(present_hr), len(missing_hr), len(present_tech), len(missing_tech)]
    ax.bar(categories, values, color=["green", "red", "blue", "orange"])
    ax.set_ylabel("Count of Skills")
    ax.set_title("Resume vs JD Skills (Zero-Shot Categorized)")
    st.pyplot(fig)

    # ---------------- Navigation ----------------
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.page_index = 0
            st.switch_page("Home.py")
    with col2:
        if st.button("Next ➡️"):
            st.session_state.page_index = 2
            st.switch_page("pages/2_Preparation_Path.py")
