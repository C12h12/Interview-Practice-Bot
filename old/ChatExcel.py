# ============================================================
# 🔹 Streamlit + Excel Interview Prep Chatbot (RAG + Mistral API)
# ============================================================
import streamlit as st
from streamlit_chat import message
import time
import requests
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.title("📊 Excel Interview Preparation Chatbot")

# ----------------------------
# Ensure skill data is loaded
# ----------------------------
if "selected_skill" not in st.session_state or "skill_data" not in st.session_state:
    st.warning("⚠️ No skill loaded. Please go back and load a skill first.")
    st.stop()

selected_skill = st.session_state.selected_skill
skill_data = st.session_state.skill_data   # 🔹 Your Excel JSON structure

# ----------------------------
# Initialize chat history
# ----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if selected_skill not in st.session_state.chat_history:
    st.session_state.chat_history[selected_skill] = []

# Show welcome message once
if not st.session_state.chat_history[selected_skill]:
    welcome_msg = f"👋 Welcome! I’ll act as your Excel interview coach.\n\nLet's practice {selected_skill}. I’ll ask you interview-style questions, you try to answer, and I’ll give feedback."
    st.session_state.chat_history[selected_skill].append({"bot": welcome_msg})

# ============================================================
# 1. Build Knowledge Base (Cached)
# ============================================================
@st.cache_resource
def build_knowledge_base(skill_data):
    docs = []
    metadata = []

    # Topics
    for topic in skill_data.get("topics", []):
        docs.append(f"Topic: {topic}")
        metadata.append({"type": "topic", "name": topic})

    # Functions + sub-functions
    for fn in skill_data.get("functions", []):
        fn_name = fn.get("name", "")
        fn_desc = fn.get("description", "")
        docs.append(f"Function: {fn_name}\nDescription: {fn_desc}")
        metadata.append({"type": "function", "name": fn_name})

        for sub_fn in fn.get("sub_functions", []):
            sub_name = sub_fn.get("name", "")
            sub_desc = sub_fn.get("description", "")
            examples = "\n".join(sub_fn.get("examples", []))
            doc_text = f"Sub-function: {sub_name}\nDescription: {sub_desc}\nExamples:\n{examples}"
            docs.append(doc_text)
            metadata.append({"type": "sub_function", "name": sub_name})

    # Create embeddings
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(docs, show_progress_bar=False, convert_to_numpy=True)
    return docs, metadata, model, embeddings

faq_documents, document_metadata, sentence_model, document_embeddings = build_knowledge_base(skill_data)

# ============================================================
# 2. Retrieval (Cached)
# ============================================================
@st.cache_data(show_spinner=False)
def retrieve_relevant_documents(query: str, top_k: int = 3, similarity_threshold: float = 0.1):
    query_embedding = sentence_model.encode([query], convert_to_numpy=True)
    similarities = cosine_similarity(query_embedding, document_embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = similarities[idx]
        if score >= similarity_threshold:
            results.append({
                "document": faq_documents[idx],
                "score": float(score),
                "metadata": document_metadata[idx],
                "index": int(idx)
            })
    return results

# ============================================================
# 3. Mistral API (Cached)
# ============================================================
MISTRAL_API_KEY = "0C9jyqEUMOzvkQzgrVV8mascDfrfU1Tf"   # 🔑 replace with your key
API_URL = "https://api.mistral.ai/v1/chat/completions"

@st.cache_data(show_spinner=False)
def call_mistral_api(prompt: str, model="mistral-small-latest", temperature=0.8, max_tokens=350):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},  # required
        {"role": "user", "content": prompt}
    ],
    "temperature": temperature,
    "max_tokens": max_tokens
}


    for attempt in range(3):  # retry if rate-limited
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 429:
            wait_time = 2 ** attempt
            time.sleep(wait_time)
            continue
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    raise RuntimeError("❌ Mistral API failed after retries.")

# ============================================================
# 4. RAG Response
# ============================================================
def generate_interview_question(query: str):
    retrieved_docs = retrieve_relevant_documents(query, top_k=3)
    context = "No relevant info found." if not retrieved_docs else "\n\n".join([doc["document"] for doc in retrieved_docs])

    prompt = f"""
You are an Excel interview coach.
Context (Excel knowledge): {context}

User just answered: {query}

Now:
- Ask the NEXT interview-style question.
- Keep it clear and concise (1 sentence).
- Do NOT add praise or feedback.
- Do NOT repeat "Great!".
Return ONLY the question.
"""
    return call_mistral_api(prompt)


# ============================================================
# 4b. LLM Feedback on User Answer (Q + A only)
# ============================================================
def generate_feedback(user_input: str, selected_skill: str):
    # Find the last asked question
    last_question = None
    for msg in reversed(st.session_state.chat_history[selected_skill]):
        if "bot" in msg and msg["bot"].startswith("❓ Next Question"):
            last_question = msg["bot"].replace("❓ Next Question:", "").strip()
            break

    # If no previous question, skip feedback
    if not last_question:
        return None  

    feedback_prompt = f"""
You are an Excel interview coach.
Interview Question:
{last_question}

User's Answer:
{user_input}

Instructions:
- Give feedback on how well the user's answer addressed the specific question above.
- Keep it **1–2 sentences, clear and conversational**.
- Do NOT start with "Great!" or repeat "Great! Great!".
- If correct → acknowledge briefly and add a tip.
- If partially correct → point out gaps and clarify.
- If wrong → politely correct with the right knowledge.
Return ONLY feedback (no follow-up question).
"""
    return call_mistral_api(feedback_prompt)


# ============================================================
# 6. Display Chat with Styling
# ============================================================
for i, msg in enumerate(st.session_state.chat_history[selected_skill]):
    if "user" in msg:
        message(msg["user"], is_user=True, key=f"user_{i}")
    else:
        bot_msg = msg["bot"]

        if bot_msg.startswith("📝 Feedback"):
            st.info(bot_msg)      # blue box
        elif bot_msg.startswith("❓ Next Question"):
            st.success(bot_msg)   # green box
        else:
            message(bot_msg, key=f"bot_{i}")

# ============================================================
# 5. Chat Interface (Fixed to avoid duplicate responses)
# ============================================================

# Store last processed input
if "last_user_input" not in st.session_state:
    st.session_state.last_user_input = None

user_input = st.text_input("💬 Your Answer or Ask Me:", key=f"user_input_{selected_skill}")

if user_input and user_input != st.session_state.last_user_input:
    # Step 1: Save user input
    st.session_state.chat_history[selected_skill].append({"user": user_input})

    # Step 2: Generate feedback only if a question exists
    feedback = generate_feedback(user_input, selected_skill)
    if feedback:  # Only add if not None
        st.session_state.chat_history[selected_skill].append({"bot": f"📝 Feedback: {feedback}"})

    # Step 3: Generate next question
    next_question = generate_interview_question(user_input)
    st.session_state.chat_history[selected_skill].append({"bot": f"❓ Next Question: {next_question}"})

    # Update last processed input
    st.session_state.last_user_input = user_input

    st.rerun()


