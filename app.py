import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import (
    ERROR_MESSAGE,
    MAX_HISTORY_MESSAGES,
    MAX_MESSAGE_LENGTH,
    MAX_OUTPUT_TOKENS,
    MODEL_NAME,
    SYSTEM_PROMPT,
    TEMPERATURE,
)

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_contents(history):
    contents = []
    for item in history[-MAX_HISTORY_MESSAGES:]:
        role = item.get("role")
        text = str(item.get("text", "")).strip()
        if role in ("user", "model") and text:
            contents.append(
                types.Content(role=role, parts=[types.Part(text=text[:MAX_MESSAGE_LENGTH])])
            )
    return contents


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    contents = build_contents(data.get("history", []))

    if not contents or contents[-1].role != "user":
        return jsonify({"error": "Please send a message."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        )
        reply = (response.text or "").strip() or ERROR_MESSAGE
        return jsonify({"reply": reply})
    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify({"error": ERROR_MESSAGE}), 500


if __name__ == "__main__":
    app.run(debug=True)
