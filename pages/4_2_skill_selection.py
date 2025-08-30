import streamlit as st
import os

st.title("Technical Skills Improvement Quiz + Chatbot")

# ----------------------------
# Ensure missing_tech exists
# ----------------------------
if "missing_tech" not in st.session_state or not st.session_state.missing_tech:
    st.warning("⚠️ No missing skills found. Please complete the Skill Comparison first.")
    st.stop()

missing_tech = st.session_state.missing_tech

# ----------------------------
# Step 1: Select skill
# ----------------------------
selected_skill = st.selectbox("Select a skill to load:", missing_tech)

# ----------------------------
# Step 2: Initialize skill in session_state
# ----------------------------
if selected_skill:
    # Save selected skill in session_state
    st.session_state.selected_skill = selected_skill

    # Initialize conversation for this skill if not already
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.success(f"Skill '{selected_skill}' selected. You can now start chatting!")

    # Redirect to chatbot page
    st.switch_page("pages/general_chatbot.py")
