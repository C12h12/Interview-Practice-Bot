import streamlit as st

st.title("Choose Your Preparation Path")

col1, col2 = st.columns(2)
with col1:
    if st.button("💼 HR Interview ➡️"):
        st.session_state.page_index = 3
        st.switch_page("pages/3_HR.py")

with col2:
    if st.button("🖥 Technical Interview ➡️"):
        st.session_state.page_index = 4
        st.switch_page("pages/4_Technical.py")

if st.button("⬅️ Back"):
    st.session_state.page_index = 1
    st.switch_page("pages/1_Skill_Comparison.py")
