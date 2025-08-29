import streamlit as st

st.title("Choose Your Preparation Path")

# Store the selected path (HR / Technical) in session state
if "prep_path" not in st.session_state:
    st.session_state.prep_path = None

col1, col2 = st.columns(2)
with col1:
    if st.button("💼 HR Interview ➡️"):
        st.session_state.prep_path = "HR"
        st.session_state.page_index = 3
        st.switch_page("pages/3_HR.py")

with col2:
    if st.button("🖥 Technical Interview ➡️"):
        st.session_state.prep_path = "Technical"
        st.session_state.page_index = 4
        st.switch_page("pages/4_Technical.py")

if st.button("⬅️ Back"):
    st.session_state.page_index = 1
    st.switch_page("pages/1_Skill_Comparison.py")

# Optional: Display cached choice
if st.session_state.prep_path:
    st.info(f"📌 You last selected: **{st.session_state.prep_path} Interview**")
