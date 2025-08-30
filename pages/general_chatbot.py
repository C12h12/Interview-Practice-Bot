import streamlit as st
import requests
import time
from streamlit_chat import message

st.set_page_config(page_title="Technical Skills Interview Chatbot")
st.title("📊 Technical Skills Interview Chatbot")

# ----------------------------
# Ensure skill is loaded
# ----------------------------
if "selected_skill" not in st.session_state:
    st.warning("⚠️ No skill loaded. Go back and select a skill first.")
    st.stop()

selected_skill = st.session_state.selected_skill

# ----------------------------
# Initialize chat history in session_state
# ----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ----------------------------
# Display welcome message if empty
# ----------------------------
if not st.session_state.chat_history:
    welcome_msg = (
        f"👋 Hello! I’m your {selected_skill} coach.\n"
        "You can ask me anything, prepare for interviews, solve your doubts…"
    )
    st.session_state.chat_history.append({"bot": welcome_msg})

# ----------------------------
# Display chat messages
# ----------------------------
for i, msg in enumerate(st.session_state.chat_history):
    if "user" in msg:
        message(msg["user"], is_user=True, key=f"user_{i}")
    else:
        message(msg["bot"], key=f"bot_{i}")

# ----------------------------
# Mistral API call
# ----------------------------
MISTRAL_API_KEY = "0C9jyqEUMOzvkQzgrVV8mascDfrfU1Tf"
API_URL = "https://api.mistral.ai/v1/chat/completions"

def call_mistral_api(prompt: str, model="mistral-small-latest", temperature=0.8, max_tokens=350):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"You are an expert {selected_skill} interview coach."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    for attempt in range(3):
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    raise RuntimeError("Mistral API failed after retries.")

# ----------------------------
# Handle user input (with automatic clearing)
# ----------------------------
def handle_user_input():
    user_input = st.session_state[f"user_input_{selected_skill}"]
    if not user_input:
        return

    # Prevent duplicate processing
    if "last_input" not in st.session_state or st.session_state.last_input != user_input:
        st.session_state.last_input = user_input

        # Save user message
        st.session_state.chat_history.append({"user": user_input})

        # Prepare prompt for LLM
        prompt = (
            f"Previous conversation:\n{st.session_state.chat_history}\n\n"
            f"User input: {user_input}\n\n"
            "Respond intelligently: either ask the next interview question, answer the user's doubt, "
            "provide information, or give feedback. Keep responses clear and concise."
        )

        # Call Mistral API
        bot_response = call_mistral_api(prompt)
        st.session_state.chat_history.append({"bot": bot_response})

        # Clear the input safely
        st.session_state[f"user_input_{selected_skill}"] = ""

# ----------------------------
# Chat Input
# ----------------------------
st.text_input(
    f"💬 Ask me anything about {selected_skill}:",
    key=f"user_input_{selected_skill}",
    on_change=handle_user_input
)
