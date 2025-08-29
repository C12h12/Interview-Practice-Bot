import streamlit as st

st.title("HR Interview Preparation")
st.write("Here you can practice HR-related questions based on your skills.")

# Ensure HR skills are available in session_state
if "present_hr" not in st.session_state or "missing_hr" not in st.session_state:
    st.warning("⚠️ Please complete the Skill Comparison first.")
else:
    # Cache results into local variables
    present_hr = st.session_state.get("present_hr", set())
    missing_hr = st.session_state.get("missing_hr", set())

    # Store them again (just to ensure persistence if user reloads)
    st.session_state.present_hr = present_hr
    st.session_state.missing_hr = missing_hr

    st.subheader("✅ HR Skills you already have:")
    st.write(", ".join(present_hr) if present_hr else "None")

    st.subheader("❌ HR Skills you should focus on:")
    st.write(", ".join(missing_hr) if missing_hr else "None")

# Navigation button
if st.button("⬅️ Back"):
    st.session_state.page_index = 2
    st.switch_page("pages/2_Preparation_Path.py")
