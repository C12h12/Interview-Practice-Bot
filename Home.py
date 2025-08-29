import streamlit as st
from NLP_skills_extract import read_file

st.set_page_config(page_title="Interview Preparation Chatbot", layout="centered")

st.title("Interview Preparation Chatbot")

# ---------------- Caching ----------------
@st.cache_data
def process_uploaded_file(uploaded_file):
    """Reads and processes uploaded files using your NLP function."""
    return read_file(uploaded_file)

# ---------------- Session State ----------------
if "page_index" not in st.session_state:
    st.session_state.page_index = 0   # 0 = Home

if "jd_file" not in st.session_state:
    st.session_state.jd_file = None
if "resume_file" not in st.session_state:
    st.session_state.resume_file = None

if "show_uploads" not in st.session_state:
    st.session_state.show_uploads = False

# ---------------- UI ----------------
if not st.session_state.show_uploads:
    if st.button("Want to prepare for Interview"):
        st.session_state.show_uploads = True

if st.session_state.show_uploads:
    st.subheader("Upload your files for preparation")

    jd_file = st.file_uploader("Upload Job Description (JD)", type=["txt", "pdf", "docx"])
    resume_file = st.file_uploader("Upload Resume", type=["txt", "pdf", "docx"])

    if jd_file and resume_file:
        st.success("✅ Files uploaded successfully! Ready to process 🚀")
        st.session_state.jd_file = jd_file
        st.session_state.resume_file = resume_file

        # Process files only once (cached)
        jd_text = process_uploaded_file(jd_file)
        resume_text = process_uploaded_file(resume_file)

        if st.button("Next ➡️"):
            st.session_state.page_index = 1   # move to Skill Comparison
            st.switch_page("pages/1_Skill_Comparison.py")
