import streamlit as st
import json

st.title("Technical Skills Improvement Quiz + Chatbot")

# ----------------------------
# Ensure missing_tech exists
# ----------------------------
if "missing_tech" not in st.session_state or not st.session_state.missing_tech:
    st.warning("⚠️ No missing skills found. Please complete the Skill Comparison first.")
    st.stop()

missing_tech = st.session_state.missing_tech

# ----------------------------
# Map skills to JSON files
# ----------------------------
skill_files = {
    "Excel": "JSON/excel.json",
    "Communication": "contexts/communication.json",
    "Power BI": "contexts/powerbi.json",
    "Algorithms": "contexts/algorithms.json",
    "Teamwork": "contexts/teamwork.json",
    "TypeScript": "contexts/typescript.json",
    "Kubernetes": "contexts/kubernetes.json"
}
# Map skills to their respective chat pages
chat_pages = {
    "Excel": "pages/ChatExcel.py",
    "Communication": "pages/chat_communication.py",
    "Power BI": "pages/chat_powerbi.py",
    "Algorithms": "pages/chat_algorithms.py",
    "Teamwork": "pages/chat_teamwork.py",
    "TypeScript": "pages/chat_typescript.py",
    "Kubernetes": "pages/chat_kubernetes.py"
}

# ----------------------------
# Cache JSON loader
# ----------------------------
@st.cache_data
def load_skill_file(file_path: str):
    """Load and parse a skill JSON file, cache so it’s reused across reruns."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------
# Step 1: Select skill
# ----------------------------
selected_skill = st.selectbox("Select a skill to load:", missing_tech)

# ----------------------------
# Step 2: Load JSON file
# ----------------------------
if st.button("Load Skill File"):
    file_path = skill_files.get(selected_skill)
    chat_page = chat_pages.get(selected_skill)  # get the corresponding chat page

    if file_path and chat_page:
        try:
            st.session_state.skill_data = load_skill_file(file_path)  # ✅ cached
            st.session_state.selected_skill = selected_skill
            st.success(f"Loaded JSON for {selected_skill} successfully!")

            # Navigate directly to the correct chat page
            st.switch_page(chat_page)

        except FileNotFoundError:
            st.error(f"File not found: {file_path}")
        except json.JSONDecodeError:
            st.error(f"Invalid JSON in file: {file_path}")
    else:
        st.error("No file or chat page mapped for this skill.")
