from flask import Flask, render_template, request, redirect, url_for, session
from utils.nlp_skills import read_file, extract_skills_smart, BASE_SKILLS
from transformers import pipeline
import requests, time

app = Flask(__name__)
app.secret_key = "supersecretkey"  # session handling

# -------------------------------
# Load HuggingFace model once
# -------------------------------
classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")
candidate_labels = ["HR", "Technical"]

classifier = None

def get_classifier():
    global classifier
    if classifier is None:
        from transformers import pipeline
        classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")
    return classifier

def categorize_skills(skills):
    if not skills:
        return set(), set()
    
    clf = get_classifier()
    results = clf(list(skills), candidate_labels=["HR", "Technical"])  # batch call

    hr_set, tech_set = set(), set()
    # HuggingFace returns list if multiple inputs, dict if single
    if isinstance(results, dict):
        results = [results]

    for skill, result in zip(skills, results):
        if result["labels"][0] == "HR":
            hr_set.add(skill)
        else:
            tech_set.add(skill)

    return hr_set, tech_set



# ---------------- Routes ----------------
@app.route("/test")
def test():
    return "<h1>Flask is working ✅</h1>"


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/skill_comparison", methods=["GET", "POST"])
def skill_comparison():
    if request.method == "POST":
        jd_file = request.files["jd_file"]
        resume_file = request.files["resume_file"]

        # Read text from uploaded files
        jd_text = read_file(jd_file)
        resume_text = read_file(resume_file)

        jd_skills = extract_skills_smart(jd_text, BASE_SKILLS)
        resume_skills = extract_skills_smart(resume_text, BASE_SKILLS)

        missing_skills = jd_skills - resume_skills
        present_skills = jd_skills & resume_skills

        present_hr, present_tech = categorize_skills(present_skills)
        missing_hr, missing_tech = categorize_skills(missing_skills)

        session["present_hr"] = list(present_hr)
        session["present_tech"] = list(present_tech)
        session["missing_hr"] = list(missing_hr)
        session["missing_tech"] = list(missing_tech)

        return redirect(url_for("prep_path"))

    return render_template("skill_comparison.html")


@app.route("/prep_path")
def prep_path():
    return render_template("prep_path.html")


@app.route("/hr")
def hr():
    return render_template(
        "hr.html",
        present_hr=session.get("present_hr", []),
        missing_hr=session.get("missing_hr", [])
    )


@app.route("/technical")
def technical():
    return render_template(
        "technical.html",
        present_tech=session.get("present_tech", []),
        missing_tech=session.get("missing_tech", [])
    )


# ---------------- Chatbot ----------------
MISTRAL_API_KEY = "T6M1qfonf8ZdC8jZwHmKckbOVVSTneaZ"  # replace with your actual key
API_URL = "https://api.mistral.ai/v1/chat/completions"

def call_mistral_api(prompt, skill_context, model="mistral-small-latest"):
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"You are an expert technical interview coach. The candidate is missing these technical skills: {skill_context}. Help them prepare."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 350
    }
    for attempt in range(3):
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    return "⚠️ API error, please try again."

import re

def clean_response(text):
    # remove markdown bold/italics
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  
    text = re.sub(r"\*(.*?)\*", r"\1", text)      
    # remove bullet points / extra formatting
    text = text.replace("•", "").replace("-", "")
    # collapse multiple newlines into one
    text = re.sub(r"\n+", "\n", text).strip()
    return text



@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    # Always reset chat on new load (if you want it fresh each time)
    if request.method == "GET":
        session.pop("chat_history", None)
        session.pop("last_input", None)
    # ----------------------------
    # Focus only on missing TECH skills
    # ----------------------------
    missing_tech = session.get("missing_tech", [])
    skill_context = ", ".join(missing_tech) if missing_tech else "general technical skills"

    # ----------------------------
    # Initialize chat history
    # ----------------------------
    if "chat_history" not in session:
        session["chat_history"] = []

    chat_history = session["chat_history"]

    # ----------------------------
    # Welcome message
    # ----------------------------
    if not chat_history:
        welcome_msg = (
    f"👋 I see you’re missing: {skill_context}.\n"
    "Don’t worry, I’ve got you!\n\n"
)
        welcome_msg_2 = ("❓ You can ask me anything.\n"
    "📝 Quiz you when needed.\n"
    "💡 Share feedback right away.")

        chat_history.append({"bot": welcome_msg})
        chat_history.append({"bot": welcome_msg_2})
        session["chat_history"] = chat_history

    # ----------------------------
    # Handle user input
    # ----------------------------
    if request.method == "POST":
        user_input = request.form.get("user_input", "").strip()
        if user_input:
            if session.get("last_input") != user_input:
                session["last_input"] = user_input

                chat_history.append({"user": user_input})

                prompt = (
    f"Conversation so far:\n{chat_history}\n\n"
    f"User: {user_input}\n\n"
    "You are a technical interview coach. "
    "Answer in plain text only (no Markdown, no asterisks, no formatting). "
    "Keep replies short, 1–2 sentences, clear and direct. "
    "After answering, always ask a simple follow-up question or suggest what the user should try next."
)



                bot_response = call_mistral_api(prompt, skill_context)
                bot_response = clean_response(bot_response)  # sanitize
                chat_history.append({"bot": bot_response})

                session["chat_history"] = chat_history

    return render_template("chatbot.html", chat_history=chat_history, skill_context=skill_context)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
