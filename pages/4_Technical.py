import streamlit as st

st.title("Technical Interview Preparation")
st.write("Here you can practice technical questions based on your skills.")

# ----------------------------
# Cache skill state loader
# ----------------------------
@st.cache_data
def load_skill_state(present_tech, missing_tech):
    """Return present and missing skills (cached)."""
    return present_tech, missing_tech

# ----------------------------
# Check if the required session_state variables exist
# ----------------------------
if "present_tech" not in st.session_state or "missing_tech" not in st.session_state:
    st.warning("⚠️ Please complete the Skill Comparison first.")
else:
    present_tech, missing_tech = load_skill_state(
        st.session_state.present_tech,
        st.session_state.missing_tech
    )

    st.subheader("✅ Technical Skills you already have:")
    st.write(", ".join(present_tech) if present_tech else "None")

    st.subheader("❌ Technical Skills you should focus on:")
    st.write(", ".join(missing_tech) if missing_tech else "None")

    # ----------------------------
    # Button to start quiz
    # ----------------------------
    if missing_tech:  # only if there are missing skills
        if st.button("▶️ Start Quiz"):
            st.session_state.page_index = 3  # or any index for the quiz page
            st.switch_page("pages/4_T_Skill_selection.py")  # replace with your actual quiz page file
    else:
        st.info("All skills are present! No quiz needed.")

# ----------------------------
# Navigation back
# ----------------------------
if st.button("⬅️ Back"):
    st.session_state.page_index = 2
    st.switch_page("pages/2_Preparation_Path.py")
